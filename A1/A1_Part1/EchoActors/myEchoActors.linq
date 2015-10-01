<Query Kind="Program">
  <Reference Relative="System.Threading.Tasks.Dataflow.dll">C:\Uni of Auckland\CS711\A1\EchoActors\System.Threading.Tasks.Dataflow.dll</Reference>
  <Namespace>System.Threading.Tasks</Namespace>
  <Namespace>System.Threading.Tasks.Dataflow</Namespace>
</Query>

// ---

void Main() {
	//read Network.txt
	
	var lines = File.ReadAllLines("Echocase2.txt")
					.Select(line=>line.Split((String[])null, StringSplitOptions.RemoveEmptyEntries)
									  .Select(s => int.Parse(s))
									  .ToArray()); 

	
	//first line
	var nodes = lines.First();
	//remaining lines
	var edges = lines.Skip(1);
	
	Network.Init(nodes, edges);
    var sw = Stopwatch.StartNew();
    Network.Start().Wait();
    sw.Stop();


	Console.WriteLine("total time {0} ms", sw.ElapsedMilliseconds);
	Console.WriteLine("node count {0}", Node.Vertex.Count);
	Console.WriteLine("edge count {0}", Node.EdgeCount);
	Console.WriteLine("message count {0}", Node.MessageCount);
	Console.WriteLine("\n");
    
	
	Console.WriteLine("Node  Parent");
	foreach (int k in Node.Vertex.Keys)
		Console.WriteLine("{0}     {1}", Node.Vertex[k].Nid, Node.Vertex[k].Parent);
	
}

// ---

protected internal sealed class Network {

	static int source = 0;
	
	static internal void Init(int[] nodelist, IEnumerable<int[]> edgelist)
	{
        
		Node.Reset(); 
		
		source = nodelist.First();
		
		new InitiatorNode(source); 
		
		foreach(int node in nodelist.Skip(1))
		{
			new CommonNode(node); 
		}
    
		/*	
		//find max delay
		ArrayList alldelays = new ArrayList();
		foreach (int[] edge in edgelist)
		{
			//put all delays into one list and sort them to get the max one.
			var delays = edge.Skip(2);
		    int maxdelayofedge = delays.Max();
			alldelays.Add(maxdelayofedge);
		}
		
		alldelays.Sort();
		int maxdelay = (int)alldelays[alldelays.Count-1];

		
		//build link/edge
        foreach (int[] edge in edgelist)
		{
			
			if(edge.ElementAt(2) != 0)
			{
				edge[2] = maxdelay;
			}
			
			if(edge.ElementAt(3) != 0)
			{
				edge[3] = maxdelay;
			}
		
			
		    Node.Link(edge.ElementAt(0), edge.ElementAt(1), edge.ElementAt(2), edge.ElementAt(3));  
		}
		*/
		foreach (int[] edge in edgelist)
		{
			Node.Link(edge.ElementAt(0), edge.ElementAt(1), edge.ElementAt(2), edge.ElementAt(3)); 
		}
	}


    static internal async Task Start() {
    
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

    protected internal int Code;
	protected internal int SubtreeSize;
    
    protected internal EchoMessage(int code, int subtreesize) {
        Code = code;
		SubtreeSize = subtreesize;
    }
	

    public override string ToString() {
        return string.Format("{0} {1}", Code, SubtreeSize);
    }
}

protected internal class EchoNode: Node {
    static protected internal readonly int MSG_DIRECT = 0;
    static protected internal readonly int MSG_REFLECT = 1;
	//instance variable
	protected internal int size = 0;
    
    protected internal EchoNode(int nid): base(nid) {
    }
}

protected internal class InitiatorNode: EchoNode {
    protected internal InitiatorNode(int nid): base(nid) {

    }

    protected internal override async Task<object> Run() {
     //   Init();
		size = 1;
        
        foreach (int n in NeighDelay.Keys) {
            //await 
            PostAsync(new EchoMessage(MSG_DIRECT, 0), n, NeighDelay[n]);
        }
        
        int rec = 0;
        var count = NeighDelay.Count();
        
        while (rec < count) {
            var ntok = await ReceiveAsync();
			EchoMessage msg = (EchoMessage)ntok.Item2;
            rec += 1;
			
			if (msg.Code == MSG_REFLECT)
				size += msg.SubtreeSize;
        }

		if (TRACE_THREAD) 
			Console.Write("[{0}] ", TID());
		
		Console.WriteLine("\n");
        Console.WriteLine("source {0} decides size: {1} ", Nid, size);
        return Nid;
    }
}

protected internal class CommonNode: EchoNode {

    protected internal CommonNode(int nid): base(nid) {

    }

    protected internal override async Task<object> Run() {
       // Init();

        var ptok = await ReceiveAsync();
        Parent = ptok.Item1;
	
        if (TRACE_PARENT) {
            if (TRACE_THREAD) Console.Write("[{0}] ", TID());
            Console.WriteLine("{0} => {1}", Parent, Nid);
        }
		
        foreach (int n in NeighDelay.Keys) {
            if (n != Parent) 
			{
                //await 
                PostAsync(new EchoMessage(MSG_DIRECT, 0), n, NeighDelay[n]);
			}
        }
        
        int rec = 1;
        var count = NeighDelay.Count();
        
        while (rec < count) {
            var ntok = await ReceiveAsync();
			EchoMessage msg = (EchoMessage)ntok.Item2;
			if (msg.Code == MSG_REFLECT)
			{
				size += msg.SubtreeSize;
			}
			
            rec += 1;
			
        }
        
        int dly = NeighDelay[Parent];
        //await 
        size += 1;
        PostAsync(new EchoMessage(MSG_REFLECT, size), Parent, dly);
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
       // MessageCount += 1;
		Interlocked.Increment(ref MessageCount);
        
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