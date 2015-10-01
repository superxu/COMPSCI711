<Query Kind="Program">
  <Reference Relative="System.Threading.Tasks.Dataflow.dll">C:\Uni of Auckland\CS711\A1\Cidon\System.Threading.Tasks.Dataflow.dll</Reference>
  <Namespace>System</Namespace>
  <Namespace>System.Collections</Namespace>
  <Namespace>System.Collections.Generic</Namespace>
  <Namespace>System.Diagnostics</Namespace>
  <Namespace>System.IO</Namespace>
  <Namespace>System.Linq</Namespace>
  <Namespace>System.Text</Namespace>
  <Namespace>System.Threading</Namespace>
  <Namespace>System.Threading.Tasks</Namespace>
  <Namespace>System.Threading.Tasks.Dataflow</Namespace>
</Query>

void Main(string[] args)
{
       //read Network.txt
       var lines = File.ReadAllLines("Cidoncase1.txt")
                       .Select(line => line.Split((String[])null, StringSplitOptions.RemoveEmptyEntries)
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


      // Console.ReadLine();

}



protected internal sealed class Network
{

  static int source = 0;

  static internal void Init(int[] nodelist, IEnumerable<int[]> edgelist)
  {

      Node.Reset();

      source = nodelist.First();

      new InitiatorNode(source);

      foreach (int node in nodelist.Skip(1))
      {
          new CommonNode(node);
      }


      //build link/edge
      foreach (int[] edge in edgelist)
      {
          Node.Link(edge.ElementAt(0), edge.ElementAt(1), edge.ElementAt(2), edge.ElementAt(3));
      }

  }


  static internal async Task Start()
  {

      var tasks = new List<Task>();

      // source should run first
      Node.Vertex[source].Run();

      foreach (int nid in Node.Vertex.Keys)
      {
          if (nid != source)
              tasks.Add(Node.Vertex[nid].Run()); // no await yet!
      }


      await Task.WhenAll(tasks);
  }
}

   // --- your actual Echo implementation ---

protected internal class EchoMessage
{

  protected internal int Code;
  protected internal int SubtreeSize;

  protected internal EchoMessage(int code, int subtreesize)
  {
      Code = code;
      SubtreeSize = subtreesize;
  }


  public override string ToString()
  {
      return string.Format("{0} {1}", Code, SubtreeSize);
  }
}

protected internal class EchoNode : Node
{
  //message type
  static protected internal readonly int MSG_NOTIFY = 0; // notify others that I've been visited
  static protected internal readonly int MSG_FORWARD = 1; //token
  static protected internal readonly int MSG_REFLECT = 2; //backward
  //node state
  static protected internal readonly int STATE_IDLE = 0; // inactive
  static protected internal readonly int STATE_DISCOVERED = 1; // active

  static protected internal readonly int LINK_UNVISITED = 0;
  static protected internal readonly int LINK_VISITED = 1;
  static protected internal readonly int LINK_FATHER = 2;
  static protected internal readonly int LINK_SON = 3;

  //instance variable
  protected internal int size = 0;
  protected internal int state = 0;
  protected internal bool found_son = false;
  protected internal int notification_count = 0;
  protected internal int backward_count = 0;
  protected internal Dictionary<int, int> Mark_j = new Dictionary<int, int>();

  protected internal EchoNode(int nid)
      : base(nid)
  {

  }
}

protected internal class InitiatorNode : EchoNode
{


  protected internal InitiatorNode(int nid)
      : base(nid)
  {
      size = 1;
      state = STATE_IDLE;
  }


  protected internal bool Search()
  {
      //SEARCH
      foreach (int node in Mark_j.Keys)
      {
          if ((Mark_j[node] == LINK_UNVISITED))
          {
              PostAsync(new EchoMessage(MSG_FORWARD, 0), node, NeighDelay[node]);
              Mark_j[node] = LINK_SON;
              found_son = true;
              break;
          }

      }

      return found_son;

  }


  protected internal override async Task<object> Run()
  {
      //   Init();
      state = STATE_DISCOVERED;

      foreach (int n in NeighDelay.Keys)
      {
          Mark_j.Add(n, LINK_UNVISITED);
      }


      //tell all my neighbours that I've been visited
      foreach (int n in NeighDelay.Keys)
      {
          //await 
          if ((Mark_j[n] == LINK_VISITED) || (Mark_j[n] == LINK_UNVISITED))
              PostAsync(new EchoMessage(MSG_NOTIFY, 0), n, NeighDelay[n]);
      }
	   
	   
	    //SEARCH
      foreach (int node in Mark_j.Keys)
      {
          if ((Mark_j[node] == LINK_UNVISITED))
          {
              PostAsync(new EchoMessage(MSG_FORWARD, 0), node, NeighDelay[node]);
              Mark_j[node] = LINK_SON;
              break;
          }

      }


      int rec = 0;
      var count = NeighDelay.Count();

      while (rec < count)
      {
          var ntok = await ReceiveAsync();
          EchoMessage msg = (EchoMessage)ntok.Item2;
          rec += 1;

          if (msg.Code == MSG_REFLECT)
          {
              size += msg.SubtreeSize;
          }
		   else if(msg.Code == MSG_NOTIFY)
		   {
		   	   if (Mark_j[ntok.Item1] == LINK_UNVISITED)
              {
                  Mark_j[ntok.Item1] = LINK_VISITED;
              }
		   }
		   else
		   {
		  		// SEARCH					
		  		if(Search() == false)
		       		break;
		   	
		   }
		   
	
			   

      }

      if (TRACE_THREAD)
          Console.Write("[{0}] ", TID());

      Console.WriteLine("\n");
      Console.WriteLine("source {0} decides size: {1} ", Nid, size);
      return Nid;
  }
}

protected internal class CommonNode : EchoNode
{

  protected internal CommonNode(int nid)
      : base(nid)
  {
      size = 1;
      state = STATE_IDLE;
  }


  protected internal bool Search()
  {
      //SEARCH
      foreach (int node in Mark_j.Keys)
      {
          if ((Mark_j[node] == LINK_UNVISITED) && (node != Parent))
          {
              PostAsync(new EchoMessage(MSG_FORWARD, 0), node, NeighDelay[node]);
              Mark_j[node] = LINK_SON;
              found_son = true;
              break;
          }

      }

      if (found_son == false)
      {
          if ((notification_count + backward_count) < NeighDelay.Count())
		  {
			  return true;
		  }
		  else
          {
              //send TOKEN over k for which marki(k) = father
              foreach (int node in Mark_j.Keys)
              {
                  if (Mark_j[node] == LINK_FATHER)
                  {
                      PostAsync(new EchoMessage(MSG_REFLECT, size), node, NeighDelay[node]);
                      break;
                  }
              }

              return false;
          }

      }

      return true;

  }

  protected internal override async Task<object> Run()
  {
      // Init();

      foreach (int n in NeighDelay.Keys)
      {
          Mark_j.Add(n, LINK_UNVISITED);
      }


      if (TRACE_PARENT)
      {
          if (TRACE_THREAD) Console.Write("[{0}] ", TID());
      }


      bool keep_running = true;
      while (keep_running)
      {
          found_son = false;
          var ntok = await ReceiveAsync();
          EchoMessage msg_b = (EchoMessage)ntok.Item2;
          //if I got a token, tell my neighbours
          if (msg_b.Code == MSG_FORWARD)
          {
              if (state == STATE_IDLE)
              {
                  state = STATE_DISCOVERED;
                  Parent = ntok.Item1;
                  Mark_j[Parent] = LINK_FATHER;

                  // Send notification before SEARCH
                  foreach (int n in NeighDelay.Keys)
                  {
                      if ((Mark_j[n] == LINK_VISITED) || (Mark_j[n] == LINK_UNVISITED))
                      {
                          PostAsync(new EchoMessage(MSG_NOTIFY, 0), n, NeighDelay[n]);
                      }
                  }


                  //SEARCH
                  if (Search() == false)
                  {
                      keep_running = false;
                  }


              }
              else //STATE_DISCOVERED
              {
                  if (Mark_j[ntok.Item1] == LINK_UNVISITED)
                  {
                      Mark_j[ntok.Item1] = LINK_VISITED;
                  }


                  if (Mark_j[ntok.Item1] == LINK_SON)
                  {
                      //SEARCH
                      if (Search() == false)
                      {
                          keep_running = false;
                      }

                  }

              }
          }
          else if (msg_b.Code == MSG_NOTIFY)
          {
              notification_count++;

              if (Mark_j[ntok.Item1] == LINK_UNVISITED)
              {
                  Mark_j[ntok.Item1] = LINK_VISITED;
              }

              if ((Mark_j[ntok.Item1] == LINK_SON) || (Mark_j[ntok.Item1] == LINK_FATHER))
              {

                  //SEARCH
                  if (Search() == false)
                  {
                      keep_running = false;
                  }

              }


          }
          else //MSG_REFLECT
          {
			  // a common node, i.e. node 3 may have more than one sub tree.
              size += msg_b.SubtreeSize;
			  backward_count++;
			  
              if (msg_b.Code == MSG_REFLECT)
              {
                  if (Mark_j[ntok.Item1] == LINK_UNVISITED)
                  {
                      Mark_j[ntok.Item1] = LINK_VISITED;
                  }

                  if (Mark_j[ntok.Item1] == LINK_SON)
                  {
                      //SEARCH
                      if (Search() == false)
                      {
                          keep_running = false;
                      }

                  }

              }
          }

      }

      return Nid;
  }
}

// ===========================================================
// Please do NOT touch this library
// ===========================================================

static protected internal int TID() { return Thread.CurrentThread.ManagedThreadId; }

protected internal class Node
{
  // static members

  static protected internal bool TRACE_THREAD = false;
  static protected internal bool TRACE_INIT = true;
  static protected internal bool TRACE_POST = false;
  static protected internal bool TRACE_RECEIVE = true;
  static protected internal bool TRACE_PARENT = false;

  static protected internal Dictionary<int, Node> Vertex = new Dictionary<int, Node>();
  static protected internal int EdgeCount = 0;
  static protected internal int MessageCount = 0;

  static protected internal void Reset()
  {
      Vertex = new Dictionary<int, Node>();
      EdgeCount = 0;
      MessageCount = 0;
  }

  static protected internal void Link(int nid1, int nid2, int del12, int del21)
  {
      EdgeCount += 1;
      Vertex[nid1].NeighDelay[nid2] = del12;
      Vertex[nid2].NeighDelay[nid1] = del21;
  }

  // instance members

  protected internal int Parent = 0;
  protected internal int Nid;
  protected internal Dictionary<int, int> NeighDelay = new Dictionary<int, int>();

  protected internal Node(int nid)
  {
      Nid = nid;
      Vertex[nid] = this;
  }

  public override string ToString()
  {
      var ns = NeighDelay.Keys.Aggregate("", (a, n) => a + n + ":" + NeighDelay[n] + ", ");
      return string.Format("<Nid:{0}, Parent:{1}, NeighDelay=({2})>",
          Nid, Parent, ns);
  }

  protected internal virtual void Init()
  {
      if (TRACE_INIT)
      {
          if (TRACE_THREAD) Console.Write("[{0}] ", TID());
          Console.WriteLine("{0}", this);
      }
  }

  protected internal virtual async Task<object> Run()
  {
      return null;
  }

  protected internal BufferBlock<Tuple<int, object, int>> inbox = new BufferBlock<Tuple<int, object, int>>();

  protected internal async Task<bool> PostAsync(object tok, int nid2, int dly2)
  {
      // MessageCount += 1;
      Interlocked.Increment(ref MessageCount);

      if (TRACE_POST)
      {
          if (TRACE_THREAD) Console.Write("[{0}] ", TID());
          Console.WriteLine("{0} -> [{1}] ... {2}:{3}", Nid, tok, nid2, dly2);
      }

      await Task.Delay(dly2);
      return Vertex[nid2].inbox.Post(Tuple.Create(Nid, tok, dly2));
  }

  protected internal async Task<Tuple<int, object, int>> ReceiveAsync()
  {
      var ntok = await inbox.ReceiveAsync();

      if (TRACE_RECEIVE)
      {
          if (TRACE_THREAD) Console.Write("[{0}] ", TID());
          Console.WriteLine("{0} -> [{1}] -> {2}:{3}", ntok.Item1, ntok.Item2, Nid, ntok.Item3);
      }

      return ntok;
  }
}