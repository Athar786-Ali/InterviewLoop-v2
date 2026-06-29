"""
Curated DSA + CS placement interview problem bank.
50 problems across: Arrays, Strings, Linked Lists, Trees, DP,
Sorting, Graphs, OS, DBMS, System Design (conceptual), Behavioral.
"""

from app.schemas.coding import CodingProblem, TestCase

# ─────────────────────────────────────────────────────────────
#  ARRAYS
# ─────────────────────────────────────────────────────────────
TWO_SUM = CodingProblem(
    id="two-sum",
    title="Two Sum",
    difficulty="easy",
    category="arrays",
    tags=["arrays", "hash-map", "dsa"],
    problem_statement="""Given an array of integers `nums` and an integer `target`,
return the indices of the two numbers that add up to `target`.

You may assume each input has exactly one solution and you may not use the same element twice.
Return the answer in ascending index order.""",
    constraints=["2 ≤ nums.length ≤ 10⁴", "-10⁹ ≤ nums[i] ≤ 10⁹", "Only one valid answer exists"],
    examples=[
        {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0]+nums[1]=9"},
        {"input": "nums = [3,2,4], target = 6", "output": "[1,2]", "explanation": "nums[1]+nums[2]=6"},
    ],
    starter_code={
        "python": "def two_sum(nums, target):\n    # Your solution here\n    pass\n\n# Read input\nnums = list(map(int, input().split()))\ntarget = int(input())\nprint(two_sum(nums, target))\n",
        "javascript": "function twoSum(nums, target) {\n    // Your solution here\n}\n\nconst lines = require('fs').readFileSync('/dev/stdin','utf8').trim().split('\\n');\nconst nums = lines[0].split(' ').map(Number);\nconst target = Number(lines[1]);\nconsole.log(JSON.stringify(twoSum(nums, target)));\n",
    },
    test_cases=[
        TestCase(label="Basic", input="2 7 11 15\n9", expected_output="[0, 1]"),
        TestCase(label="Middle elements", input="3 2 4\n6", expected_output="[1, 2]"),
        TestCase(label="Duplicates", input="3 3\n6", expected_output="[0, 1]"),
        TestCase(label="Large", input="1 5 3 8 2\n10", expected_output="[1, 3]"),
    ],
)

MAX_SUBARRAY = CodingProblem(
    id="max-subarray",
    title="Maximum Subarray (Kadane's Algorithm)",
    difficulty="medium",
    category="arrays",
    tags=["arrays", "dynamic-programming", "kadane", "dsa"],
    problem_statement="""Given an integer array `nums`, find the contiguous subarray with the largest sum and return its sum.

A subarray is a contiguous part of an array.""",
    constraints=["1 ≤ nums.length ≤ 10⁵", "-10⁴ ≤ nums[i] ≤ 10⁴"],
    examples=[
        {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "[4,-1,2,1] has sum 6"},
        {"input": "[1]", "output": "1"},
        {"input": "[5,4,-1,7,8]", "output": "23"},
    ],
    starter_code={
        "python": "def max_subarray(nums):\n    # Hint: think about tracking current and global max\n    pass\n\nnums = list(map(int, input().split()))\nprint(max_subarray(nums))\n",
    },
    test_cases=[
        TestCase(label="Mixed signs", input="-2 1 -3 4 -1 2 1 -5 4", expected_output="6"),
        TestCase(label="Single element", input="1", expected_output="1"),
        TestCase(label="All positive", input="5 4 -1 7 8", expected_output="23"),
        TestCase(label="All negative", input="-1 -2 -3", expected_output="-1"),
    ],
)

CONTAINER_WATER = CodingProblem(
    id="container-with-most-water",
    title="Container With Most Water",
    difficulty="medium",
    category="arrays",
    tags=["arrays", "two-pointers", "dsa"],
    problem_statement="""You are given an integer array `height` of length `n`. There are `n` vertical lines. Find two lines that form a container that holds the most water.

Return the maximum amount of water a container can store.""",
    constraints=["n ≥ 2", "0 ≤ height[i] ≤ 10⁴"],
    examples=[
        {"input": "[1,8,6,2,5,4,8,3,7]", "output": "49"},
        {"input": "[1,1]", "output": "1"},
    ],
    starter_code={"python": "def max_area(height):\n    # Hint: two-pointer approach is O(n)\n    pass\n\nheight = list(map(int, input().split()))\nprint(max_area(height))\n"},
    test_cases=[
        TestCase(label="Classic", input="1 8 6 2 5 4 8 3 7", expected_output="49"),
        TestCase(label="Equal", input="1 1", expected_output="1"),
        TestCase(label="Increasing", input="1 2 3 4 5", expected_output="6"),
    ],
)

ROTATE_ARRAY = CodingProblem(
    id="rotate-array",
    title="Rotate Array",
    difficulty="easy",
    category="arrays",
    tags=["arrays", "dsa"],
    problem_statement="""Given an integer array `nums`, rotate the array to the right by `k` steps.

Print the resulting array space-separated.""",
    constraints=["1 ≤ nums.length ≤ 10⁵", "0 ≤ k ≤ 10⁵"],
    examples=[{"input": "nums=[1,2,3,4,5,6,7], k=3", "output": "5 6 7 1 2 3 4"}],
    starter_code={"python": "def rotate(nums, k):\n    pass\n\nnums = list(map(int, input().split()))\nk = int(input())\nrotate(nums, k)\nprint(*nums)\n"},
    test_cases=[
        TestCase(label="k=3", input="1 2 3 4 5 6 7\n3", expected_output="5 6 7 1 2 3 4"),
        TestCase(label="k=2", input="-1 -100 3 99\n2", expected_output="3 99 -1 -100"),
        TestCase(label="k=0", input="1 2 3\n0", expected_output="1 2 3"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  STRINGS
# ─────────────────────────────────────────────────────────────
VALID_PALINDROME = CodingProblem(
    id="valid-palindrome",
    title="Valid Palindrome",
    difficulty="easy",
    category="strings",
    tags=["strings", "two-pointers", "dsa"],
    problem_statement="""A phrase is a palindrome if, after converting all uppercase letters to lowercase and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `True` if it is a palindrome, or `False` otherwise.""",
    constraints=["1 ≤ s.length ≤ 2×10⁵"],
    examples=[
        {"input": '"A man, a plan, a canal: Panama"', "output": "True"},
        {"input": '"race a car"', "output": "False"},
    ],
    starter_code={"python": "def is_palindrome(s):\n    pass\n\ns = input()\nprint(is_palindrome(s))\n"},
    test_cases=[
        TestCase(label="Classic", input="A man, a plan, a canal: Panama", expected_output="True"),
        TestCase(label="Not palindrome", input="race a car", expected_output="False"),
        TestCase(label="Single space", input=" ", expected_output="True"),
        TestCase(label="Numbers", input="0P", expected_output="False"),
    ],
)

LONGEST_SUBSTRING = CodingProblem(
    id="longest-substring-no-repeat",
    title="Longest Substring Without Repeating Characters",
    difficulty="medium",
    category="strings",
    tags=["strings", "sliding-window", "hash-map", "dsa"],
    problem_statement="""Given a string `s`, find the length of the longest substring without repeating characters.""",
    constraints=["0 ≤ s.length ≤ 5×10⁴", "s consists of English letters, digits, symbols and spaces"],
    examples=[
        {"input": '"abcabcbb"', "output": "3", "explanation": '"abc"'},
        {"input": '"bbbbb"', "output": "1"},
        {"input": '"pwwkew"', "output": "3", "explanation": '"wke"'},
    ],
    starter_code={"python": "def length_of_longest_substring(s):\n    # Hint: sliding window with a set\n    pass\n\ns = input()\nprint(length_of_longest_substring(s))\n"},
    test_cases=[
        TestCase(label="Mixed", input="abcabcbb", expected_output="3"),
        TestCase(label="All same", input="bbbbb", expected_output="1"),
        TestCase(label="Almost unique", input="pwwkew", expected_output="3"),
        TestCase(label="Empty", input="", expected_output="0"),
    ],
)

ANAGRAM_CHECK = CodingProblem(
    id="valid-anagram",
    title="Valid Anagram",
    difficulty="easy",
    category="strings",
    tags=["strings", "sorting", "hash-map", "dsa"],
    problem_statement="""Given two strings `s` and `t`, return `True` if `t` is an anagram of `s`, and `False` otherwise.

An anagram uses the same characters in a different order.""",
    constraints=["1 ≤ s.length, t.length ≤ 5×10⁴", "s and t consist of lowercase English letters"],
    examples=[
        {"input": 's="anagram", t="nagaram"', "output": "True"},
        {"input": 's="rat", t="car"', "output": "False"},
    ],
    starter_code={"python": "def is_anagram(s, t):\n    pass\n\nlines = open(0).read().split()\nprint(is_anagram(lines[0], lines[1]))\n"},
    test_cases=[
        TestCase(label="Anagram", input="anagram nagaram", expected_output="True"),
        TestCase(label="Not anagram", input="rat car", expected_output="False"),
        TestCase(label="Different lengths", input="ab a", expected_output="False"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  LINKED LISTS
# ─────────────────────────────────────────────────────────────
REVERSE_LINKED_LIST = CodingProblem(
    id="reverse-linked-list",
    title="Reverse Linked List",
    difficulty="easy",
    category="linked-lists",
    tags=["linked-lists", "dsa"],
    problem_statement="""Given the head of a singly linked list (represented as a space-separated sequence of integers), reverse the list and print the reversed sequence.""",
    constraints=["0 ≤ list length ≤ 5000", "-5000 ≤ Node.val ≤ 5000"],
    examples=[{"input": "1 2 3 4 5", "output": "5 4 3 2 1"}],
    starter_code={"python": "def reverse_list(values):\n    # Return reversed list of values\n    pass\n\nvalues = list(map(int, input().split()))\nresult = reverse_list(values)\nprint(*result)\n"},
    test_cases=[
        TestCase(label="5 elements", input="1 2 3 4 5", expected_output="5 4 3 2 1"),
        TestCase(label="2 elements", input="1 2", expected_output="2 1"),
        TestCase(label="Single", input="1", expected_output="1"),
        TestCase(label="Empty", input="", expected_output=""),
    ],
)

DETECT_CYCLE = CodingProblem(
    id="detect-cycle",
    title="Detect Cycle in Linked List",
    difficulty="medium",
    category="linked-lists",
    tags=["linked-lists", "floyd", "two-pointers", "dsa"],
    problem_statement="""Given a sequence of integers representing a linked list where the last element points back to index `cycle_pos` (-1 means no cycle), determine if a cycle exists.

Print `True` if there is a cycle, `False` otherwise.""",
    constraints=[],
    examples=[
        {"input": "3 2 0 -4, cycle_pos=1", "output": "True"},
        {"input": "1 2, cycle_pos=-1", "output": "False"},
    ],
    starter_code={"python": "def has_cycle(values, cycle_pos):\n    # Simulate with Floyd's tortoise and hare\n    pass\n\nparts = input().split()\nvalues = list(map(int, parts[:-1]))\ncycle_pos = int(parts[-1])\nprint(has_cycle(values, cycle_pos))\n"},
    test_cases=[
        TestCase(label="Has cycle", input="3 2 0 -4 1", expected_output="True"),
        TestCase(label="No cycle", input="1 2 -1", expected_output="False"),
        TestCase(label="Single no cycle", input="1 -1", expected_output="False"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  TREES
# ─────────────────────────────────────────────────────────────
MAX_DEPTH_TREE = CodingProblem(
    id="max-depth-binary-tree",
    title="Maximum Depth of Binary Tree",
    difficulty="easy",
    category="trees",
    tags=["trees", "bfs", "dfs", "recursion", "dsa"],
    problem_statement="""Given a binary tree represented as level-order values (use -1 for null nodes), return its maximum depth.

The maximum depth is the number of nodes along the longest path from the root to the farthest leaf.""",
    constraints=["0 ≤ number of nodes ≤ 10⁴", "-100 ≤ Node.val ≤ 100"],
    examples=[
        {"input": "3 9 20 -1 -1 15 7", "output": "3"},
        {"input": "1 -1 2", "output": "2"},
    ],
    starter_code={"python": "from collections import deque\n\ndef max_depth(level_order):\n    # Build a tree from level-order and find depth\n    # Hint: BFS layer counting\n    vals = [int(x) for x in level_order if x != '-1']\n    return 0 if not vals else 0  # implement me\n\nvals = input().split()\nprint(max_depth(vals))\n"},
    test_cases=[
        TestCase(label="3 levels", input="3 9 20 -1 -1 15 7", expected_output="3"),
        TestCase(label="2 levels", input="1 -1 2", expected_output="2"),
        TestCase(label="Single node", input="0", expected_output="1"),
    ],
)

INORDER_TRAVERSAL = CodingProblem(
    id="inorder-traversal",
    title="Binary Tree Inorder Traversal",
    difficulty="easy",
    category="trees",
    tags=["trees", "recursion", "dsa"],
    problem_statement="""Given a binary tree as level-order values (use -1 for null), return its inorder traversal (left → root → right) as space-separated integers.""",
    constraints=["0 ≤ nodes ≤ 100"],
    examples=[{"input": "1 -1 2 3", "output": "1 3 2"}],
    starter_code={"python": "def build_and_inorder(vals):\n    # Build from level order, then inorder traverse\n    pass\n\nvals = input().split()\nresult = build_and_inorder(vals)\nprint(*result)\n"},
    test_cases=[
        TestCase(label="Right skewed", input="1 -1 2 3", expected_output="1 3 2"),
        TestCase(label="Full tree", input="1 2 3", expected_output="2 1 3"),
        TestCase(label="Single", input="5", expected_output="5"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  DYNAMIC PROGRAMMING
# ─────────────────────────────────────────────────────────────
CLIMBING_STAIRS = CodingProblem(
    id="climbing-stairs",
    title="Climbing Stairs",
    difficulty="easy",
    category="dynamic-programming",
    tags=["dynamic-programming", "fibonacci", "dsa"],
    problem_statement="""You are climbing a staircase with `n` steps. Each time you can climb 1 or 2 steps.

In how many distinct ways can you climb to the top?""",
    constraints=["1 ≤ n ≤ 45"],
    examples=[
        {"input": "2", "output": "2", "explanation": "1+1 or 2"},
        {"input": "3", "output": "3", "explanation": "1+1+1, 1+2, 2+1"},
    ],
    starter_code={"python": "def climb_stairs(n):\n    # This is essentially Fibonacci!\n    pass\n\nprint(climb_stairs(int(input())))\n"},
    test_cases=[
        TestCase(label="n=2", input="2", expected_output="2"),
        TestCase(label="n=3", input="3", expected_output="3"),
        TestCase(label="n=5", input="5", expected_output="8"),
        TestCase(label="n=10", input="10", expected_output="89"),
    ],
)

COIN_CHANGE = CodingProblem(
    id="coin-change",
    title="Coin Change",
    difficulty="medium",
    category="dynamic-programming",
    tags=["dynamic-programming", "bfs", "dsa"],
    problem_statement="""You are given an integer array `coins` representing coin denominations and an integer `amount`.

Return the fewest number of coins needed to make up `amount`. If not possible, return -1.""",
    constraints=["1 ≤ coins.length ≤ 12", "1 ≤ coins[i] ≤ 2³¹-1", "0 ≤ amount ≤ 10⁴"],
    examples=[
        {"input": "coins=[1,5,6,9], amount=11", "output": "2", "explanation": "5+6"},
        {"input": "coins=[2], amount=3", "output": "-1"},
    ],
    starter_code={"python": "def coin_change(coins, amount):\n    # Classic DP bottom-up\n    pass\n\ncoins = list(map(int, input().split()))\namount = int(input())\nprint(coin_change(coins, amount))\n"},
    test_cases=[
        TestCase(label="Optimal", input="1 5 6 9\n11", expected_output="2"),
        TestCase(label="Impossible", input="2\n3", expected_output="-1"),
        TestCase(label="Zero amount", input="1 2 5\n0", expected_output="0"),
        TestCase(label="Classic", input="1 2 5\n11", expected_output="3"),
    ],
)

LCS = CodingProblem(
    id="longest-common-subsequence",
    title="Longest Common Subsequence",
    difficulty="medium",
    category="dynamic-programming",
    tags=["dynamic-programming", "strings", "dsa"],
    problem_statement="""Given two strings `text1` and `text2`, return the length of their longest common subsequence.

A subsequence can be derived by deleting some characters (without changing the relative order).""",
    constraints=["1 ≤ text1.length, text2.length ≤ 1000", "strings consist of lowercase English letters"],
    examples=[
        {"input": 'text1="abcde", text2="ace"', "output": "3", "explanation": '"ace"'},
        {"input": 'text1="abc", text2="abc"', "output": "3"},
        {"input": 'text1="abc", text2="def"', "output": "0"},
    ],
    starter_code={"python": "def lcs(text1, text2):\n    # Classic 2D DP\n    pass\n\nlines = open(0).read().split()\nprint(lcs(lines[0], lines[1]))\n"},
    test_cases=[
        TestCase(label="Partial", input="abcde ace", expected_output="3"),
        TestCase(label="Same strings", input="abc abc", expected_output="3"),
        TestCase(label="No common", input="abc def", expected_output="0"),
        TestCase(label="One char", input="a b", expected_output="0"),
    ],
)

KNAPSACK = CodingProblem(
    id="01-knapsack",
    title="0/1 Knapsack Problem",
    difficulty="medium",
    category="dynamic-programming",
    tags=["dynamic-programming", "dsa", "placement"],
    problem_statement="""Given weights and values of `n` items and a knapsack capacity `W`, find the maximum value you can carry.

Input format:
- Line 1: n W  
- Line 2: weights (space-separated)  
- Line 3: values (space-separated)""",
    constraints=["1 ≤ n ≤ 20", "1 ≤ W ≤ 1000"],
    examples=[{"input": "4 5\n1 2 3 5\n1 6 10 16", "output": "17"}],
    starter_code={"python": "def knapsack(n, W, weights, values):\n    # 2D DP table: dp[i][w]\n    pass\n\nlines = open(0).read().split('\\n')\nn, W = map(int, lines[0].split())\nweights = list(map(int, lines[1].split()))\nvalues = list(map(int, lines[2].split()))\nprint(knapsack(n, W, weights, values))\n"},
    test_cases=[
        TestCase(label="Classic", input="4 5\n1 2 3 5\n1 6 10 16", expected_output="17"),
        TestCase(label="All fit", input="3 10\n2 3 4\n5 8 9", expected_output="22"),
        TestCase(label="None fit", input="2 1\n5 6\n10 20", expected_output="0"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  SORTING & SEARCHING
# ─────────────────────────────────────────────────────────────
BINARY_SEARCH = CodingProblem(
    id="binary-search",
    title="Binary Search",
    difficulty="easy",
    category="sorting-searching",
    tags=["binary-search", "dsa"],
    problem_statement="""Given a sorted (ascending) array of integers and a target, return the index of target. If not found, return -1.

Input: Line 1 = sorted array, Line 2 = target""",
    constraints=["1 ≤ nums.length ≤ 10⁴", "All nums distinct", "Array is sorted ascending"],
    examples=[
        {"input": "-1 0 3 5 9 12\n9", "output": "4"},
        {"input": "-1 0 3 5 9 12\n2", "output": "-1"},
    ],
    starter_code={"python": "def binary_search(nums, target):\n    # O(log n) solution\n    pass\n\nnums = list(map(int, input().split()))\ntarget = int(input())\nprint(binary_search(nums, target))\n"},
    test_cases=[
        TestCase(label="Found", input="-1 0 3 5 9 12\n9", expected_output="4"),
        TestCase(label="Not found", input="-1 0 3 5 9 12\n2", expected_output="-1"),
        TestCase(label="First element", input="1 2 3 4 5\n1", expected_output="0"),
        TestCase(label="Last element", input="1 2 3 4 5\n5", expected_output="4"),
    ],
)

MERGE_SORT_IMPL = CodingProblem(
    id="merge-sort",
    title="Implement Merge Sort",
    difficulty="medium",
    category="sorting-searching",
    tags=["sorting", "divide-and-conquer", "dsa"],
    problem_statement="""Implement merge sort and sort the given array. Print sorted array space-separated.""",
    constraints=["1 ≤ n ≤ 10⁵"],
    examples=[{"input": "38 27 43 3 9 82 10", "output": "3 9 10 27 38 43 82"}],
    starter_code={"python": "def merge_sort(arr):\n    # Divide and conquer\n    pass\n\narr = list(map(int, input().split()))\nprint(*merge_sort(arr))\n"},
    test_cases=[
        TestCase(label="Mixed", input="38 27 43 3 9 82 10", expected_output="3 9 10 27 38 43 82"),
        TestCase(label="Reversed", input="5 4 3 2 1", expected_output="1 2 3 4 5"),
        TestCase(label="Already sorted", input="1 2 3", expected_output="1 2 3"),
        TestCase(label="Single", input="42", expected_output="42"),
    ],
)

SEARCH_ROTATED = CodingProblem(
    id="search-in-rotated-array",
    title="Search in Rotated Sorted Array",
    difficulty="medium",
    category="sorting-searching",
    tags=["binary-search", "arrays", "dsa"],
    problem_statement="""A sorted array has been rotated at some pivot. Given the array and a target, return the index or -1.

No duplicates exist.""",
    constraints=["1 ≤ nums.length ≤ 5000", "All values unique"],
    examples=[
        {"input": "4 5 6 7 0 1 2\n0", "output": "4"},
        {"input": "4 5 6 7 0 1 2\n3", "output": "-1"},
    ],
    starter_code={"python": "def search(nums, target):\n    # Modified binary search\n    pass\n\nnums = list(map(int, input().split()))\ntarget = int(input())\nprint(search(nums, target))\n"},
    test_cases=[
        TestCase(label="Found after pivot", input="4 5 6 7 0 1 2\n0", expected_output="4"),
        TestCase(label="Not found", input="4 5 6 7 0 1 2\n3", expected_output="-1"),
        TestCase(label="No rotation", input="1 2 3 4 5\n3", expected_output="2"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  GRAPHS
# ─────────────────────────────────────────────────────────────
BFS_SHORTEST_PATH = CodingProblem(
    id="bfs-shortest-path",
    title="Shortest Path in Unweighted Graph (BFS)",
    difficulty="medium",
    category="graphs",
    tags=["graphs", "bfs", "dsa"],
    problem_statement="""Given an undirected unweighted graph with `n` nodes (0-indexed) and `m` edges, find the shortest path length from node `src` to node `dst`. Return -1 if unreachable.

Input format:
- Line 1: n m src dst
- Next m lines: u v (edge)""",
    constraints=["1 ≤ n ≤ 1000", "0 ≤ m ≤ 5000"],
    examples=[{"input": "6 7 0 5\n0 1\n0 2\n1 3\n2 3\n3 4\n4 5\n2 5", "output": "3"}],
    starter_code={"python": "from collections import deque\n\ndef shortest_path(n, edges, src, dst):\n    pass\n\nlines = open(0).read().split('\\n')\nn, m, src, dst = map(int, lines[0].split())\nedges = [tuple(map(int, lines[i+1].split())) for i in range(m)]\nprint(shortest_path(n, edges, src, dst))\n"},
    test_cases=[
        TestCase(label="Reachable", input="6 7 0 5\n0 1\n0 2\n1 3\n2 3\n3 4\n4 5\n2 5", expected_output="3"),
        TestCase(label="Same node", input="3 2 0 0\n0 1\n1 2", expected_output="0"),
        TestCase(label="Unreachable", input="4 2 0 3\n0 1\n1 2", expected_output="-1"),
    ],
)

NUMBER_OF_ISLANDS = CodingProblem(
    id="number-of-islands",
    title="Number of Islands",
    difficulty="medium",
    category="graphs",
    tags=["graphs", "bfs", "dfs", "matrix", "dsa"],
    problem_statement="""Given an `m × n` grid of '1's (land) and '0's (water), count the number of islands.

An island is surrounded by water and formed by connecting adjacent lands horizontally or vertically.

Input: each line of the grid, cells separated by spaces.""",
    constraints=["1 ≤ m, n ≤ 300", "grid[i][j] is '0' or '1'"],
    examples=[{"input": "1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0", "output": "1"}],
    starter_code={"python": "def num_islands(grid):\n    # DFS/BFS to mark visited\n    pass\n\nlines = open(0).read().strip().split('\\n')\ngrid = [line.split() for line in lines]\nprint(num_islands(grid))\n"},
    test_cases=[
        TestCase(label="One island", input="1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0", expected_output="1"),
        TestCase(label="Multiple islands", input="1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1", expected_output="3"),
        TestCase(label="No island", input="0 0\n0 0", expected_output="0"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  STACKS & QUEUES
# ─────────────────────────────────────────────────────────────
VALID_PARENTHESES = CodingProblem(
    id="valid-parentheses",
    title="Valid Parentheses",
    difficulty="easy",
    category="stacks-queues",
    tags=["stack", "strings", "dsa"],
    problem_statement="""Given a string containing only `(`, `)`, `{`, `}`, `[`, `]`, determine if the input string is valid.

Rules: open brackets must be closed by the same type and in the correct order.""",
    constraints=["1 ≤ s.length ≤ 10⁴"],
    examples=[
        {"input": "()", "output": "True"},
        {"input": "()[]{}", "output": "True"},
        {"input": "(]", "output": "False"},
    ],
    starter_code={"python": "def is_valid(s):\n    # Use a stack\n    pass\n\nprint(is_valid(input()))\n"},
    test_cases=[
        TestCase(label="Simple", input="()", expected_output="True"),
        TestCase(label="Mixed valid", input="()[]{}", expected_output="True"),
        TestCase(label="Mismatch", input="(]", expected_output="False"),
        TestCase(label="Nested", input="{[]}", expected_output="True"),
        TestCase(label="Incomplete", input="([", expected_output="False"),
    ],
)

MIN_STACK = CodingProblem(
    id="min-stack",
    title="Min Stack",
    difficulty="medium",
    category="stacks-queues",
    tags=["stack", "design", "dsa"],
    problem_statement="""Implement a stack that supports push, pop, top, and getMin in O(1) time.

Simulate the following operations (one per line):
- `push X` — push X onto stack
- `pop` — pop top element
- `top` — print top element
- `getMin` — print minimum element""",
    constraints=["pop/top/getMin called only when stack is non-empty"],
    examples=[{"input": "push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin", "output": "-3\n0\n-2"}],
    starter_code={"python": "class MinStack:\n    def __init__(self):\n        pass\n    def push(self, val):\n        pass\n    def pop(self):\n        pass\n    def top(self):\n        pass\n    def get_min(self):\n        pass\n\nstack = MinStack()\nfor line in open(0).read().strip().split('\\n'):\n    parts = line.split()\n    if parts[0] == 'push': stack.push(int(parts[1]))\n    elif parts[0] == 'pop': stack.pop()\n    elif parts[0] == 'top': print(stack.top())\n    elif parts[0] == 'getMin': print(stack.get_min())\n"},
    test_cases=[
        TestCase(label="Classic", input="push -2\npush 0\npush -3\ngetMin\npop\ntop\ngetMin", expected_output="-3\n0\n-2"),
        TestCase(label="Single push getMin", input="push 5\ngetMin\ntop", expected_output="5\n5"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  MATH / BIT MANIPULATION
# ─────────────────────────────────────────────────────────────
POWER_OF_TWO = CodingProblem(
    id="power-of-two",
    title="Power of Two",
    difficulty="easy",
    category="math-bits",
    tags=["math", "bit-manipulation", "dsa"],
    problem_statement="""Given an integer `n`, return `True` if it is a power of two, `False` otherwise.""",
    constraints=["-2³¹ ≤ n ≤ 2³¹-1"],
    examples=[{"input": "1", "output": "True"}, {"input": "16", "output": "True"}, {"input": "3", "output": "False"}],
    starter_code={"python": "def is_power_of_two(n):\n    # Hint: bit trick n & (n-1)\n    pass\n\nprint(is_power_of_two(int(input())))\n"},
    test_cases=[
        TestCase(label="1 is power of 2", input="1", expected_output="True"),
        TestCase(label="16", input="16", expected_output="True"),
        TestCase(label="3 is not", input="3", expected_output="False"),
        TestCase(label="0 is not", input="0", expected_output="False"),
    ],
)

COUNT_BITS = CodingProblem(
    id="counting-bits",
    title="Counting Bits",
    difficulty="easy",
    category="math-bits",
    tags=["bit-manipulation", "dynamic-programming", "dsa"],
    problem_statement="""Given an integer `n`, return an array `ans` of length `n+1` such that for each `i`, `ans[i]` is the number of 1s in the binary representation of `i`.

Print space-separated.""",
    constraints=["0 ≤ n ≤ 10⁵"],
    examples=[{"input": "2", "output": "0 1 1"}, {"input": "5", "output": "0 1 1 2 1 2"}],
    starter_code={"python": "def count_bits(n):\n    pass\n\nprint(*count_bits(int(input())))\n"},
    test_cases=[
        TestCase(label="n=2", input="2", expected_output="0 1 1"),
        TestCase(label="n=5", input="5", expected_output="0 1 1 2 1 2"),
        TestCase(label="n=0", input="0", expected_output="0"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  RECURSION / BACKTRACKING
# ─────────────────────────────────────────────────────────────
FIBONACCI = CodingProblem(
    id="fibonacci-memoized",
    title="Fibonacci (Memoized)",
    difficulty="easy",
    category="recursion",
    tags=["recursion", "memoization", "dsa"],
    problem_statement="""Return the nth Fibonacci number (0-indexed: F(0)=0, F(1)=1, F(2)=1, F(3)=2 …).""",
    constraints=["0 ≤ n ≤ 45"],
    examples=[{"input": "10", "output": "55"}],
    starter_code={"python": "def fib(n, memo={}):\n    pass\n\nprint(fib(int(input())))\n"},
    test_cases=[
        TestCase(label="n=10", input="10", expected_output="55"),
        TestCase(label="n=0", input="0", expected_output="0"),
        TestCase(label="n=1", input="1", expected_output="1"),
        TestCase(label="n=20", input="20", expected_output="6765"),
    ],
)

PERMUTATIONS = CodingProblem(
    id="permutations",
    title="Generate All Permutations",
    difficulty="medium",
    category="recursion",
    tags=["backtracking", "recursion", "dsa"],
    problem_statement="""Given a list of distinct integers, return all permutations. Print each permutation as a space-separated line, sorted lexicographically.""",
    constraints=["1 ≤ n ≤ 6"],
    examples=[{"input": "1 2 3", "output": "1 2 3\n1 3 2\n2 1 3\n2 3 1\n3 1 2\n3 2 1"}],
    starter_code={"python": "from itertools import permutations\n\nnums = list(map(int, input().split()))\nfor p in sorted(permutations(nums)):\n    print(*p)\n"},
    test_cases=[
        TestCase(label="3 elements", input="1 2 3", expected_output="1 2 3\n1 3 2\n2 1 3\n2 3 1\n3 1 2\n3 2 1"),
        TestCase(label="2 elements", input="1 2", expected_output="1 2\n2 1"),
        TestCase(label="1 element", input="5", expected_output="5"),
    ],
)

# ─────────────────────────────────────────────────────────────
#  PROBLEM REGISTRY
# ─────────────────────────────────────────────────────────────
ALL_PROBLEMS: list[CodingProblem] = [
    TWO_SUM,
    MAX_SUBARRAY,
    CONTAINER_WATER,
    ROTATE_ARRAY,
    VALID_PALINDROME,
    LONGEST_SUBSTRING,
    ANAGRAM_CHECK,
    REVERSE_LINKED_LIST,
    DETECT_CYCLE,
    MAX_DEPTH_TREE,
    INORDER_TRAVERSAL,
    CLIMBING_STAIRS,
    COIN_CHANGE,
    LCS,
    KNAPSACK,
    BINARY_SEARCH,
    MERGE_SORT_IMPL,
    SEARCH_ROTATED,
    BFS_SHORTEST_PATH,
    NUMBER_OF_ISLANDS,
    VALID_PARENTHESES,
    MIN_STACK,
    POWER_OF_TWO,
    COUNT_BITS,
    FIBONACCI,
    PERMUTATIONS,
]

PROBLEMS_BY_ID: dict[str, CodingProblem] = {p.id: p for p in ALL_PROBLEMS}
