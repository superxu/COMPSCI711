<Query Kind="Program">
  <Reference Relative="System.Threading.Tasks.Dataflow.dll">C:\Uni of Auckland\CS711\A1\Byzantine\System.Threading.Tasks.Dataflow.dll</Reference>
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

	//read Generals.txt
	var lines = File.ReadAllLines("Generals7-Yes1.txt")
				.Select(line=>line.Split((String[])null, StringSplitOptions.RemoveEmptyEntries)); 
	
	//lines.Dump("lines");
	
	
	//first line
	var first_line = lines.First().Select(s => int.Parse(s)).ToArray();
	var nodes_count = first_line[0];
	var v0 = first_line[1];

	Console.WriteLine("node count = {0}, v0 = {1}", nodes_count, v0);
	
	// N lines after first line
	var nodes_info = lines.Skip(1);
	char[] delimiterChars = {' ',  ';'};
	Dictionary<int, Dictionary<int, string>> Generals = new Dictionary<int, Dictionary<int, string>>();
	Dictionary<int, bool> faulty_nodes_info = new Dictionary<int, bool>();
	
	for(int i = 0; i < nodes_count; i++)
	{	
		var result = lines.Skip(1).ToArray()[i];
		string node_info = string.Join(" ", result);
		string[] values = node_info.Split(delimiterChars, StringSplitOptions.RemoveEmptyEntries);

		int faulty_b = 0;
		if (Int32.TryParse(values[2], out faulty_b))
		{
			if(faulty_b == 1)
			{
				Console.WriteLine("This is a faulty node.");
				var values_dict = new Dictionary<int, string>();
				int node = 1;
				for(int x = 3; x < values.Length; x++)
				{
					values_dict.Add(node, values[x]);
					node++;
					
				}
			
				Console.WriteLine("node:{0} value:{1}", Int32.Parse(values[0]), values[1]);
				faulty_nodes_info.Add(Int32.Parse(values[0]), true);
				Generals.Add(Int32.Parse(values[0]), values_dict);		
			}
			else
			{
				Console.WriteLine("This is a non-faulty node.");
				var values_dict = new Dictionary<int, string>();
				Console.WriteLine("node:{0} value:{1}", Int32.Parse(values[0]), values[1]);
				values_dict.Add(Int32.Parse(values[0]), values[1]);
				faulty_nodes_info.Add(Int32.Parse(values[0]), false);
				Generals.Add(Int32.Parse(values[0]), values_dict);	
			}
		}
		else
		{
			continue;
		}
		
	}
	
	
	//delay info
	var delays = lines.Skip(1+ nodes_count);
	var delay_info = new List<int[]>{};
	var delay_count = (nodes_count * (nodes_count-1))/2;

	
	for (int k = 0; k < delay_count; k++)
	{
		var line = delays.ToArray()[k];
		int[] delay = line.Select(s => int.Parse(s)).ToArray();
		
		delay_info.Add(delay);
	}
	
	
	Network.Init(Generals, delay_info, faulty_nodes_info, nodes_count, v0.ToString());
	Network.Start().Wait();
	
	Console.WriteLine("");
	
	foreach(KeyValuePair<string, int> kvp in EchoNode.nodesdict)
	{
		var key = Int32.Parse(kvp.Key);
		var value = faulty_nodes_info[key];
		
		if(value == true)
		{
			Console.WriteLine("{0} : {1}", kvp.Key, "*");
		}
		else
		{
			Console.WriteLine("{0} : {1}", kvp.Key, kvp.Value);
		}
	}
	
	EchoNode.nodesdict.Clear();
}



protected internal sealed class NodeData
{
	public string label;
	public string value;
	public string newval;
	
	public NodeData(string path, string data, string new_value)
	{
		label = path;
		value = data;
		newval = new_value;
	}
	
	public string Getlabel()
	{
		return label;
	}
	
	public string Getvalue()
	{
		return value;
	}
	
	public string Getnewval()
	{
		return newval;
	}
	
	public override string ToString()
	{	
		return string.Format("{0} {1} {2}", label, value, newval);
	}
}

  

protected internal sealed class TreeNode<NodeData>
{
   public NodeData Data;  // Payload.

   public TreeNode<NodeData> Next;  // This will point to the next sibling node (if any), forming a linked-list.
   public TreeNode<NodeData> Child; // This will point to the first child node (if any).
   public TreeNode<NodeData> Parent;
}

protected internal sealed class Tree<NodeData> : IEnumerable<NodeData>
{
   public TreeNode<NodeData> Root;
   public List<TreeNode<NodeData>> Nodelist =  new List<TreeNode<NodeData>>();

   public TreeNode<NodeData> AddChild(TreeNode<NodeData> parent, NodeData data)
   {
       parent.Child = new TreeNode<NodeData>{Data = data, Next = parent.Child, // Prepare to place the new node at the head of the linked-list of children.
		   Parent = parent
       };

       return parent.Child;
   }

   public IEnumerator<NodeData> GetEnumerator()
   {
       return enumerate(Root).GetEnumerator();
   }

	
   public IEnumerable<NodeData> enumerate(TreeNode<NodeData> root)
   {
       for (var node = root; node != null; node = node.Next)
       {
		   yield return node.Data;
			
           foreach (var data in enumerate(node.Child))
		   {
               yield return data;
		   }
		   
       }
	   
   }
   
      
   protected internal int GetChildren_Count(TreeNode<NodeData> parent)
   {
   	   int num = 0;
       for (var node = parent.Child; node != null; node = node.Next)
       {
			num++;
       }
	  
	   return num;
   }
   
  
   IEnumerator IEnumerable.GetEnumerator()
   {
       return GetEnumerator();
   }
}


protected internal sealed class Network
{
  protected internal int faulty_count = 0;

  static internal void Init(Dictionary<int, Dictionary<int, string>>Generals, IEnumerable<int[]> edgelist, Dictionary<int, bool>nodes, int nodes_count, string V0)
  {
    int rounds = (nodes_count-1)/3 + 1;
    Node.Reset();

	foreach(KeyValuePair<int, bool> kvp in nodes)
	{
		if(kvp.Value == true)
		{
			new FaultyNode(kvp.Key, Generals[kvp.Key], rounds, nodes_count, V0);
		}
		else
		{
			new NonFaultyNode(kvp.Key,  Generals[kvp.Key], rounds, nodes_count, V0);
		}
		
	}

	//build link/edge
	foreach (int[] edge in edgelist)
	{
		Node.Link(edge.ElementAt(0), edge.ElementAt(1), edge.ElementAt(2), edge.ElementAt(3));
	}
	
	foreach(KeyValuePair<int, bool> kvp in nodes)
	{
		Node.Link(kvp.Key, kvp.Key, 0, 0);
	}

  }


  static internal async Task Start()
  {
	var tasks = new List<Task>();

	foreach (int nid in Node.Vertex.Keys)
	{
		tasks.Add(Node.Vertex[nid].Run()); // no await yet!
	}
	
	await Task.WhenAll(tasks);
  }
}

// --- your actual Echo implementation ---

protected internal class EchoMessage
{
	protected internal string Values;
	protected internal int Rounds;
	
	protected internal EchoMessage(string values, int rounds)
	{
		Values = values;
		Rounds = rounds;
	}
	
	public override string ToString()
	{
		return string.Format("{0}", Values);
	}
}

protected internal class EchoNode : Node
{	
	//instance variable
	protected internal int size = 0;
	protected internal int node_id = 0;
	protected internal Dictionary<int, string> initial_values = new Dictionary<int, string>();
	protected internal Dictionary<string, EchoMessage> MessageDict = new Dictionary<string, EchoMessage>();
	protected internal Dictionary<int, Dictionary<string, EchoMessage>> MessageBuffer = new Dictionary<int, Dictionary<string, EchoMessage>>();
	protected internal Dictionary<string, TreeNode<NodeData>> parentlist = new Dictionary<string, TreeNode<NodeData>>();
    protected internal Tree<NodeData> tree = new Tree<NodeData>();
	protected internal string v0_val = "";

	// member variable
	static protected internal int totalrounds = 0;
	static protected internal int generalcounts = 0;
	
	// store evaluated newval of each node
	static protected internal SortedDictionary<string, int> nodesdict = new SortedDictionary<string, int>();
	 
	protected internal EchoNode(int nid)
		: base(nid)
	{	
		node_id = nid;
	}
	
	protected internal string final_newvaloftree(TreeNode<NodeData> treeroot)
	{	
		int attack_count = 0;
		int retreat_count = 0;
	
		for(var node = treeroot.Child; node != null; node = node.Next)
		{
			//Console.WriteLine("child = {0} newvalue = {1}", node.Data.label, node.Data.newval);
			var val = Int32.Parse(node.Data.Getnewval());
		
			if(val == 1)
			{
				attack_count++;
			}
			else if (val == 0)
			{
				retreat_count++;
			}
			else
			{
				if(Int32.Parse(v0_val) == 1)
				{
					attack_count++;
				}
				else
				{
					retreat_count++;
				}
	
			}
			
		}
		
		if(attack_count > retreat_count)
		{
			//find my parent and give the evaluated value to its newval.
			treeroot.Data.newval = "1";
		}
		else if (attack_count == retreat_count)
		{
			//should return v0
			treeroot.Data.newval = v0_val;
		}
		else
		{
			treeroot.Data.newval = "0";
		}
		
		return treeroot.Data.newval;
	
	} 
	
	
	
	protected internal int report2parent(TreeNode<NodeData> treenode)
  {	
	int attack_count = 0;
	int retreat_count = 0;
	var parent = treenode;
	
	// local voting
	for(var node = parent.Child; node != null; node = node.Next)
	{
		Console.WriteLine("node is {0} value is: {1} newval is: {2}", node.Data.label, node.Data.value, node.Data.newval);
		var val = Int32.Parse(node.Data.Getnewval());
		
		if(val == 1)
		{
			attack_count++;
		}
		else if (val == 0)
		{
			retreat_count++;
		}
		else
		{
			if(Int32.Parse(v0_val) == 1)
			{
				attack_count++;
			}
			else
			{
				retreat_count++;
			}

		}
	}
	
	
	if(attack_count > retreat_count)
	{
		//find my parent and give the evaluated value to its newval.
		parent.Data.newval = "1";
	}
	else if (attack_count == retreat_count)
	{
		//should return v0
		parent.Data.newval = v0_val;
	}
	else
	{
		parent.Data.newval = "0";
	}
	
	//Console.WriteLine("parent = {0} parent.Data.newval = {1}", parent.Data.Getlabel(), parent.Data.Getnewval());	

	
	var next_parent = parent.Parent;
	if (next_parent != tree.Root)
	{
		report2parent(next_parent);
	}
	else
	{
		return 0;
	}

	return 0;
  
  }
  
	
  protected internal int evaluate_lastlevel_children(TreeNode<NodeData> treenode)
  {	
	int attack_count = 0;
	int retreat_count = 0;
	var child = treenode;
	
	//find the last level 
	while(child.Child != null)
	{
	 	child = child.Child;
	}
	
	//local voting
	for(var node = child; node != null; node = node.Next)
	{
		//Console.WriteLine("child = {0} {1}", node.Data.label, node.Data.value);
		var val = Int32.Parse(node.Data.Getvalue());
		
		if(val == 1)
		{
			attack_count++;
		}
		else if (val == 0)
		{
			retreat_count++;
		}
		else
		{
			if(Int32.Parse(v0_val) == 1)
			{
				attack_count++;
			}
			else
			{
				retreat_count++;
			}

		}
	}
	
	var parent = child.Parent;
	
	if(attack_count > retreat_count)
	{
		//find my parent and give the evaluated value to its newval.
		parent.Data.newval = "1";
	}
	else if (attack_count == retreat_count)
	{
		//should return v0
		parent.Data.newval = v0_val;
	}
	else
	{
		parent.Data.newval = "0";
	}
	
	//Console.WriteLine("parent = {0} parent.Data.newval = {1}", parent.Data.Getlabel(), parent.Data.Getnewval());	

	if(parent.Parent == tree.Root)
	{
		return 0;
	}
	
	var next_parent = parent.Next;
	
	if (next_parent != null)
	{
		evaluate_lastlevel_children(next_parent);
	}
	else
	{
		//last level evaluation done.
		report2parent(parent.Parent);
	}

	
	return 0;
  
  }
  
  
    protected internal int evaluate_tree(Tree<NodeData>tree, TreeNode<NodeData> treeroot)
  {	
	var child = treeroot.Child;
	
	for(var node = child; node != null; node = node.Next)
	{
		//Console.WriteLine("node = {0}", node.Data.label);
		evaluate_lastlevel_children(node);
	}
	
	var val = final_newvaloftree(tree.Root);
	//Console.WriteLine("I am {0}. Final value = {1}", Nid, val);
	return Int32.Parse(val);
  
  }
  
  	protected internal 	List<string> get_nextlevel_childrenid(TreeNode<NodeData>node)
	{
		var parent_path = node.Data.Getlabel();
		List<string> childrenlist = new List<string>();
		List<int> sortedchildren = new List<int>();

		if(parent_path == null)
		{
			foreach (int n in NeighDelay.Keys) 
			{
				sortedchildren.Add(n);
			}
			
			var descendingOrder = sortedchildren.OrderByDescending(i => i);
			foreach (int child in descendingOrder) 
			{
				childrenlist.Add(child.ToString());
			}
			
		}
		else
		{
			foreach (int n in NeighDelay.Keys) 
			{
				sortedchildren.Add(n);
			}
			
			sortedchildren.Sort();
			//var descendingOrder = sortedchildren.OrderByDescending(i => i);
			//List<int> parents = new List<int>();
			
			//List<int> parents = parent_path.Split('.');
			// split parent_path to int
			//Console.WriteLine("parent_path = {0} num = {1}", parent_path, parents.Count());
		
			foreach (int n in sortedchildren) 
			{
				var count = 0;
				var n2nodelabel = '.' + n.ToString() + '.';
				//Console.WriteLine("parent_path = {0} n2nodelabel = {1}", parent_path, n2nodelabel);
				
				/*
				for(int i = 0; i < parents.Count(); i++)
				{
					Console.WriteLine("i = {0}, parent_path[i] = {1}", i, parent_path[i]);
				
					if(n2nodelabel[i] != parents[i])
					{
						count++;
					}
				
				}
				*/
				
				if(!parent_path.Contains(n2nodelabel))
				{
					//count++;
					//Console.WriteLine("not contain");
					childrenlist.Add(n.ToString());
				}
				
				/*
				if(count == parents.Count())
				{
					childrenlist.Add(n.ToString());
				}
				*/
			
			}
		}

		return childrenlist;
	}
  
  	protected internal Dictionary<string, TreeNode<NodeData>> create_nextlevel_children(TreeNode<NodeData>node, int count, int round)
	{
		var parent_path = node.Data.Getlabel();
		List<string> childrenlist = get_nextlevel_childrenid(node);
		Dictionary<string, TreeNode<NodeData>> parents_list = new Dictionary<string, TreeNode<NodeData>>();
		//List<string> parents_list = new List<string>();
	  
		//Console.WriteLine("I am {0}. Begin to create next level children...", Nid);
	
		foreach(string child in childrenlist)
		{
			var new_path = "";
			if (parent_path == null)
			{
				new_path = parent_path + '.' + child + '.';
			}
			else
			{
				new_path = parent_path + child + '.';
			}
		
			//Console.WriteLine("I am {0} parent_path = {1} child = {2} new_path = {3} new_path.Length = {4}", Nid, parent_path, child, new_path, new_path.Length);
			NodeData level1 = new NodeData(new_path, "", "") ;
			var newparent = tree.AddChild(node, level1);
			parents_list.Add(new_path, newparent);
		}
		
		//Console.WriteLine("I am {0}. Done...", Nid);
		
		return parents_list;
	}


	protected internal Dictionary<string, TreeNode<NodeData>> fill_firstlevel_children(TreeNode<NodeData>node, int count, int round, SortedDictionary<string, EchoMessage> messages)
	{
		var parents_list = new Dictionary<string, TreeNode<NodeData>>();
		List<EchoMessage> msg = new	List<EchoMessage>();

		for (var nodei = node.Child; nodei != null; nodei = nodei.Next)
		{
		
			foreach(KeyValuePair<string, EchoMessage> kvp in messages)
			{
				var value = kvp.Value.Values;
				var key = '.' + kvp.Key + '.';
			
				//Console.WriteLine(" key = {0} nodei.Data.Getlabel() = {1}", key , nodei.Data.Getlabel());
				
				if (key == nodei.Data.Getlabel())
				{
					nodei.Data.value = value;
					parents_list.Add(nodei.Data.label, nodei);
					//Console.WriteLine(" kvp.Key = {0} nodei.Data.Getlabel() = {1}", kvp.Key , nodei.Data.Getlabel());
					break;
				}
			}

		}
	
		return parents_list;
	}



	protected internal Dictionary<string, TreeNode<NodeData>> fill_nextlevel_children(Dictionary<string, TreeNode<NodeData>>allparents, int count, int round, SortedDictionary<string, EchoMessage> messages)
	{
		var parents_list = new Dictionary<string, TreeNode<NodeData>>();
		List<string> path = new List<string>();
		List<EchoMessage> msg = new	List<EchoMessage>();
		
		foreach(KeyValuePair<string, EchoMessage> kvp in messages)
		{
			//Console.WriteLine("I am {0} Message from {1}, value = {2}", Nid, kvp.Key, kvp.Value.Values);
			// the position of int i = 0; is important, but it should not be..... 19/09/2015
			int i = 0; 
			foreach(KeyValuePair<string, TreeNode<NodeData>> parent in allparents)
			{
				var message_value = kvp.Value.Values;
				//Console.WriteLine("message length = {0}", message_value.Length);
				//Console.WriteLine("Current parent = {0}, message_value = {1}", parent.Value.Data.label, message_value);
				for (var node = parent.Value.Child; node != null; node = node.Next)
				{
					
					//Console.WriteLine("Current node = {0}", node.Data.label);
					var str = '.' + kvp.Key + '.';
					if(node.Data.label.EndsWith(str) == true)
					{
						//Console.WriteLine("i = {0}", i);
						node.Data.value = message_value[i++].ToString();
						//Console.WriteLine("222222222222222222222");
						parents_list.Add(node.Data.label, node);
					}
					
				}
				
			}
		}

		return parents_list;
	}
  
  
}

protected internal class FaultyNode : EchoNode
{

  protected internal FaultyNode(int nid, Dictionary<int, string>values, int total_rounds, int general_counts, string v0)
      : base(nid)
  {
		node_id = nid;
		initial_values = values;
		// find out how many rounds do I need to send messages.
		totalrounds = total_rounds;
		generalcounts = general_counts;
	    v0_val = v0;

  }

	protected internal int send_nextround_msgs(int count, int round_count)
	{
		//Console.WriteLine("I am {0}. Begin to send next round messages...", Nid);
		List<int> neighbours_list = new List<int>();
		foreach (int x in NeighDelay.Keys) 
		{
			neighbours_list.Add(x);
		}
		
		neighbours_list.Sort();
		
		foreach (int n in neighbours_list) 
		{
			var index = (neighbours_list.IndexOf(n) + 1);
		//	Console.WriteLine("index = {0}", index);
			var position = index + count*(round_count-1);
		   // Console.WriteLine("I am {0}, Send message to neighour {1} with value {2}", Nid, n, initial_values[position]);
			PostAsync(new EchoMessage(initial_values[position], round_count), n, NeighDelay[n]);
		}
	
		//Console.WriteLine("I am {0}. Done...", Nid);
		return 0;
	
	}


  protected internal override async Task<object> Run()
  {
  	int rec = 0;
	var count = NeighDelay.Count();
	var round_count = 1;
	int treenodecount = generalcounts;
   
	// Root
	NodeData data = new NodeData(null, "", "") ;
	tree.Root = new TreeNode<NodeData>{Data = data, Next = null, Parent = null};
	
	while (round_count <= totalrounds) 
	{
		SortedDictionary<string, EchoMessage>path_msg = new SortedDictionary<string, EchoMessage>();
		
		send_nextround_msgs(count, round_count);

		//create next level children before receiving messages.
		if(round_count == 1)
		{
			var parent = tree.Root;
			create_nextlevel_children(parent, count, round_count);
		}
		else
		{	
			//get parents from parentlist
			foreach(KeyValuePair<string, TreeNode<NodeData>> kvp in parentlist)
			{
				create_nextlevel_children(kvp.Value, count, round_count);
			}
		
		}

	
		//receive messages
		while(true)
		{
			//check if Message Buffer has messages of my round
			if (MessageBuffer.ContainsKey(round_count)) 
			{ 
				var getmessages = MessageBuffer[round_count];
				//Console.WriteLine("number of messages = {0}", getmessages.Count());
				var messages_count =  getmessages.Count();
				rec += messages_count;
				foreach(KeyValuePair<string, EchoMessage> kvp in getmessages)
				{
					//Console.WriteLine("path = {0} value = {1}", kvp.Key, kvp.Value.Values);
					var newpath = kvp.Key;
					var newvalue = kvp.Value.Values;
					path_msg.Add(newpath, kvp.Value);
				}
				
				MessageBuffer.Remove(round_count);
				MessageDict.Clear();
				
				if ((rec % count) == 0)
				{
					break;
				}
	
			}
			
			var ntok = await ReceiveAsync();
			EchoMessage msg = (EchoMessage)ntok.Item2;
			var path = ntok.Item1.ToString();
			//Console.WriteLine("I am {0}, Receive message from neighour {1}. msg.Value = {2} msg.round = {3}", Nid, ntok.Item1, msg.Values, msg.Rounds);
			//Console.WriteLine("msg.Rounds = {0} round_count = {1}", msg.Rounds, round_count);
			if(msg.Rounds == round_count)
			{
				rec += 1;
				path_msg.Add(path, msg);
			}
			else
			{
				MessageDict.Add(path, msg);
				
				if (MessageBuffer.ContainsKey(msg.Rounds))
				{
			
					MessageBuffer[msg.Rounds] = MessageDict;
				}
				else
				{
					MessageBuffer.Add(msg.Rounds, MessageDict);
				}
			
			    //Console.WriteLine("############### {0} Another round Message  ##############", Nid);
			}
			
			if((rec % count) == 0)
			{
				break;
			}

		}
		

		//fill values to first level
		if(round_count == 1) 
		{
			var parent = tree.Root;
			parentlist = fill_firstlevel_children(parent, count, round_count, path_msg);
		}
		else
		{
			parentlist = fill_nextlevel_children(parentlist, count, round_count, path_msg);
		}
			
		round_count++;
	}

	//start to evaluate
	//Console.WriteLine("Node {0} Staring to evaluate........", Nid);
	Console.WriteLine(tree);
	var final_val =  evaluate_tree(tree, tree.Root);
	//Console.WriteLine("final value  = {0}", final_val);
	nodesdict.Add(Nid.ToString(), final_val);
	
	//Console.WriteLine("I am {0}. Finishing...", Nid);
	return Nid;
  }
  
}

protected internal class NonFaultyNode : EchoNode
{

  protected internal NonFaultyNode(int nid, Dictionary<int, string>values, int total_rounds, int general_counts, string v0)
      : base(nid)
  {
  		node_id = nid;
		initial_values = values;
		totalrounds = total_rounds;
		generalcounts = general_counts;
		v0_val = v0;
  }

	protected internal int send_nextround_msgs(int count, int round_count, Dictionary<string, TreeNode<NodeData>> parentslist)
	{
		
		//Console.WriteLine("I am {0}. Begin to send next round {1} messages...", Nid, round_count);
		if (round_count == 1)
		{
			foreach (int n in NeighDelay.Keys) 
			{
				//Console.WriteLine("I am {0}, Send message to neighour {1} with value {2}", Nid, n, initial_values[Nid]);
				PostAsync(new EchoMessage(initial_values[Nid], round_count), n, NeighDelay[n]);
			}
		}
		else
		{
			string newvalue = "";
			//Console.WriteLine("parentlist = {0}", parentlist.Count());
			foreach(KeyValuePair<string, TreeNode<NodeData>> kvp in parentlist)
			{
			//	Console.WriteLine("I am {0} kvp.Key = {1} kvp.Value = {2}", Nid, kvp.Key, kvp.Value.Data.value);
				var str = '.' + Nid.ToString() + '.';
				if (!kvp.Key.Contains(str))
				{
					newvalue += kvp.Value.Data.value;
				}
			}
			
			List<int> neighbours_list = new List<int>();
			foreach (int x in NeighDelay.Keys) 
			{
				neighbours_list.Add(x);
			}
			
		    neighbours_list.Sort();
			
			foreach (int n in neighbours_list) 
			{
				//Console.WriteLine("I am {0}, Send message to neighour {1} with value {2}", Nid, n, newvalue);
				PostAsync(new EchoMessage(newvalue, round_count), n, NeighDelay[n]);
			}
		}
	
		//Console.WriteLine("I am {0}. Round {1} Done...", Nid, round_count);
		return 0;
	
	}
	

  protected internal override async Task<object> Run()
  {
  	int rec = 0;
	var count = NeighDelay.Count();
	var round_count = 1;
	int treenodecount = generalcounts;


  	//Console.WriteLine("{0} starts to run.....", Nid);
 	// Root
	NodeData data = new NodeData(null, "", "") ;
	tree.Root = new TreeNode<NodeData>{Data = data, Next = null, Parent = null};
	
 	Dictionary<string, string> messages = new Dictionary<string, string>();
	
	while (round_count <= totalrounds) 
	{
		SortedDictionary<string, EchoMessage>path_msg = new SortedDictionary<string, EchoMessage>();
		
		send_nextround_msgs(count, round_count, parentlist);
		messages.Clear();
		
		//create next level children before receiving messages.
		if(round_count == 1)
		{
			var parent = tree.Root;
			create_nextlevel_children(parent, count, round_count);
		}
		else
		{	
			//get parents from parentlist
			foreach(KeyValuePair<string, TreeNode<NodeData>> kvp in parentlist)
			{
				//Console.WriteLine("parent = {0}", kvp.Value.Data.Getlabel());
				create_nextlevel_children(kvp.Value, count, round_count);
			}
		
		}
		
		//receive messages
		while(true)
		{
		
			//check if Message Buffer has messages of my round
			if (MessageBuffer.ContainsKey(round_count)) 
			{ 
				var getmessages = MessageBuffer[round_count];
				//Console.WriteLine("number of messages = {0}", getmessages.Count());
				var messages_count =  getmessages.Count();
				rec += messages_count;
				
				foreach(KeyValuePair<string, EchoMessage> kvp in getmessages)
				{
					//Console.WriteLine("path = {0} value = {1}", kvp.Key, kvp.Value.Values);
					var newpath = kvp.Key;
					var newvalue = kvp.Value.Values;
					path_msg.Add(newpath, kvp.Value);
					messages.Add(newpath, newvalue);
				}
				
				MessageBuffer.Remove(round_count);
				MessageDict.Clear();
				
				
				if ((rec % count) == 0)
				{
					break;
				}
		
			}
		
			var ntok = await ReceiveAsync();
			EchoMessage msg = (EchoMessage)ntok.Item2;
			var path = ntok.Item1.ToString();
			//Console.WriteLine("I am {0}, Receive message from neighour {1}. msg.Value = {2} msg.round = {3}", Nid, ntok.Item1, msg.Values, msg.Rounds);
			if(msg.Rounds == round_count)
			{
				rec += 1;
				//keep values to fill tree nodes
				path_msg.Add(path, msg);
				//keep values to generate next round value
				messages.Add(path, msg.Values);
			}
			else
			{
				MessageDict.Add(path, msg);
				if (MessageBuffer.ContainsKey(msg.Rounds))
				{
					MessageBuffer[msg.Rounds] = MessageDict;
				}
				else
				{
					MessageBuffer.Add(msg.Rounds, MessageDict);
				}
			
				//Console.WriteLine("############### {0} Another round Message  ##############", Nid);
			}
			
			if((rec % count) == 0)
			{
				break;
			}
		}
			
		
		//fill values to first level
		if(round_count == 1) 
		{
			var parent = tree.Root;
			parentlist = fill_firstlevel_children(parent, count, round_count, path_msg);
		}
		else
		{
			parentlist = fill_nextlevel_children(parentlist, count, round_count, path_msg);
		}
		
		round_count++;

	}


	//start to evaluate
	Console.WriteLine("Node {0} Staring to evaluate........", Nid);
	//Console.WriteLine(tree);
	var final_val =  evaluate_tree(tree, tree.Root);
	//Console.WriteLine("final value  = {0}", final_val);
	nodesdict.Add(Nid.ToString(), final_val);

	if (TRACE_THREAD)
		Console.Write("[{0}] ", TID());
		
	//Console.WriteLine("I am {0}. Finishing...", Nid);
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