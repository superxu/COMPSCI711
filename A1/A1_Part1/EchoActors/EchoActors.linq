<Query Kind="Program">
  <Reference Relative="System.Threading.Tasks.Dataflow.dll">C:\Uni of Auckland\CS711\A1\EchoActors\System.Threading.Tasks.Dataflow.dll</Reference>
  <Namespace>System.Threading.Tasks</Namespace>
  <Namespace>System.Threading.Tasks.Dataflow</Namespace>
</Query>

// ---

void Main() {
    var sw = Stopwatch.StartNew();
    Network.Start().Wait();
    sw.Stop();
    sw.ElapsedMilliseconds.Dump("ElapsedMilliseconds");

    Node.Vertex.Count.Dump("NodeCount");
    Node.EdgeCount.Dump("EdgeCount");
    Node.MessageCount.Dump("MessageCount");
    
    var SpanningTree = 
        from k in Node.Vertex.Keys
        select new {Node=Node.Vertex[k].Nid, Node.Vertex[k].Parent};
    SpanningTree.Dump("SpanningTree");        
}

// ---

protected internal sealed class Network {
    static internal async Task Start() {
        Node.Reset();

        var source = 100;
        
        new InitiatorNode(source); 
        new CommonNode(200); 
        new CommonNode(300); 
        new CommonNode(400); 
    
        var maxdelay = 100;
        
        Node.Link(100, 200, 0, maxdelay);
        Node.Link(100, 300, maxdelay, 0);
        Node.Link(100, 400, maxdelay, 0);
        
        Node.Link(200, 300, 0, maxdelay);
        Node.Link(200, 400, maxdelay, 0);
        
        Node.Link(300, 400, 0, maxdelay);   
        //Node.Vertex.Dump("Node.Vertex");
    
        var tasks = new List<Task>();
        foreach (int nid in Node.Vertex.Keys) {
            if (nid != source) 
                tasks.Add(Node.Vertex[nid].Run()); // no await yet!
        }
        
        await Node.Vertex[source].Run();
        await Task.WhenAll(tasks);
    }
}

// --- your actual Echo implementation ---

protected internal class EchoMessage {
    protected internal EchoMessage(int code) {
        Code = code;
    }
    
    protected internal int Code;
    
    public override string ToString() {
        return string.Format("{0} {1}", Code,  Node.Vertex.Count);
    }
}

protected internal class EchoNode: Node {
    static protected internal readonly int MSG_DIRECT = 0;
    static protected internal readonly int MSG_REFLECT = 1;
    
    protected internal EchoNode(int nid): base(nid) {
    }
}

protected internal class InitiatorNode: EchoNode {
    protected internal InitiatorNode(int nid): base(nid) {
    }

    protected internal override async Task<object> Run() {
        Init();
        
        foreach (int n in NeighDelay.Keys) {
            //await 
            PostAsync(new EchoMessage(MSG_DIRECT), n, NeighDelay[n]);
        }
        
        int rec = 0;
        var count = NeighDelay.Count();
        
        while (rec < count) {
            var ntok = await ReceiveAsync();
            rec += 1;
        }
        
        if (TRACE_THREAD) Console.Write("[{0}] ", TID());
        Console.WriteLine("source {0} decides", Nid);
        return Nid;
    }
}

protected internal class CommonNode: EchoNode {
    protected internal CommonNode(int nid): base(nid) {
    }

    protected internal override async Task<object> Run() {
        Init();

        var ptok = await ReceiveAsync();
        Parent = ptok.Item1;
        
        if (TRACE_PARENT) {
            if (TRACE_THREAD) Console.Write("[{0}] ", TID());
            Console.WriteLine("{0} => {1}", Parent, Nid);
        }

        foreach (int n in NeighDelay.Keys) {
            if (n != Parent) 
                //await 
                PostAsync(new EchoMessage(MSG_DIRECT), n, NeighDelay[n]);
        }
        
        int rec = 1;
        var count = NeighDelay.Count();
        
        while (rec < count) {
            var ntok = await ReceiveAsync();
            rec += 1;
        }
        
        int dly = NeighDelay[Parent];
        //await 
        PostAsync(new EchoMessage(MSG_REFLECT), Parent, dly);
        return Nid;
    }
}

// ===========================================================
// Please do NOT touch this library
// ===========================================================

static protected internal int TID() { return Thread.CurrentThread.ManagedThreadId; }

protected internal class Node {
    // static members

    static protected internal bool TRACE_THREAD = false;
    static protected internal bool TRACE_INIT = true;
    static protected internal bool TRACE_POST = false;
    static protected internal bool TRACE_RECEIVE = true;
    static protected internal bool TRACE_PARENT = false;
    
    static protected internal Dictionary<int, Node> Vertex = new Dictionary<int, Node>();
    static protected internal int EdgeCount = 0;
    static protected internal int MessageCount = 0;
    
    static protected internal void Reset() {
         Vertex = new Dictionary<int, Node>();
         EdgeCount = 0;
         MessageCount = 0;
    }
    
    static protected internal void Link(int nid1, int nid2, int del12, int del21) {
        EdgeCount += 1;
        Vertex[nid1].NeighDelay[nid2] = del12;
        Vertex[nid2].NeighDelay[nid1] = del21;
    }
    
    // instance members
    
    protected internal int Parent = 0;
    protected internal int Nid;    
    protected internal Dictionary<int, int> NeighDelay = new Dictionary<int, int>();
    
    protected internal Node(int nid) {
        Nid = nid;
        Vertex[nid] = this;
    }
        
    public override string ToString() {
        var ns = NeighDelay.Keys.Aggregate("", (a,n) => a + n + ":" + NeighDelay[n] + ", ");
        return string.Format("<Nid:{0}, Parent:{1}, NeighDelay=({2})>", 
            Nid, Parent, ns);
    }
        
    protected internal virtual void Init() {
        if (TRACE_INIT) {
            if (TRACE_THREAD) Console.Write("[{0}] ", TID());
            Console.WriteLine("{0}", this);
        }
    }
    
    protected internal virtual async Task<object> Run() {
        return null;
    }
    
    protected internal BufferBlock<Tuple<int, object, int>> inbox = new BufferBlock<Tuple<int, object, int>>();    

    protected internal async Task<bool> PostAsync(object tok, int nid2, int dly2) {
        MessageCount += 1;
        
        if (TRACE_POST) {
            if (TRACE_THREAD) Console.Write("[{0}] ", TID());
            Console.WriteLine("{0} -> [{1}] ... {2}:{3}", Nid, tok, nid2, dly2);
        }
        
        await Task.Delay(dly2);
        return Vertex[nid2].inbox.Post(Tuple.Create(Nid, tok, dly2));
    }
    
    protected internal async Task<Tuple<int, object, int>> ReceiveAsync() {
        var ntok = await inbox.ReceiveAsync();
        
        if (TRACE_RECEIVE) {
            if (TRACE_THREAD) Console.Write("[{0}] ", TID());
            Console.WriteLine("{0} -> [{1}] -> {2}:{3}", ntok.Item1, ntok.Item2, Nid, ntok.Item3);
        }
        
        return ntok;
    }
}

// ---