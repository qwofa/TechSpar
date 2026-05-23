# LeetCode 算法面试速查指南

> 面试前4小时冲刺 · C# 实现 · 覆盖所有核心考点

---

## 1. 链表 (Linked List)

### 快慢指针找中点 / 环检测

#### 141. 环形链表

**题设：** 给你一个链表的头节点 `head`，判断链表中是否有环。如果链表中有某个节点，可以通过连续跟踪 `next` 指针再次到达，则链表中存在环。

```csharp
public bool HasCycle(ListNode head) {
    ListNode slow = head, fast = head;
    while (fast?.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) return true;
    }
    return false;
}
```

**解题思路：** 快指针每次走 2 步，慢指针每次走 1 步。如果链表有环，两者必然在环内某处相遇（类似追及问题）；若无环，快指针先到达 null。这是链表的必考送分题，注意 `fast?.next` 的空指针判断。

---

#### 876. 链表中点

**题设：** 给你一个长度为 `n` 的链表，返回链表的中点。如果有两个中点则返回第二个。

```csharp
public ListNode MiddleNode(ListNode head) {
    ListNode slow = head, fast = head;
    while (fast?.next?.next != null) {
        slow = slow.next;
        fast = fast.next.next;
    }
    return fast?.next == null ? slow : slow.next;
}
```

**解题思路：** 同上，快慢指针。快指针走到底时，慢指针恰好在中点。当链表长度为奇数时，循环到 `fast.next == null` 退出，此时 `slow` 就是中点；当为偶数时，循环到 `fast.next.next == null` 退出，需要返回 `slow.next`。

---

#### 234. 回文链表

**题设：** 给你一个单链表 `head`，判断是否是回文链表。要求 O(n) 时间和 O(1) 空间。

```csharp
public bool IsPalindrome(ListNode head) {
    if (head == null) return true;
    ListNode slow = head, fast = head;
    while (fast?.next?.next != null) { slow = slow.next; fast = fast.next.next; }
    ListNode second = Reverse(slow.next);
    ListNode p1 = head, p2 = second;
    while (p2 != null) {
        if (p1.val != p2.val) return false;
        p1 = p1.next; p2 = p2.next;
    }
    return true;
}
ListNode Reverse(ListNode node) {
    ListNode prev = null, cur = node;
    while (cur != null) { ListNode next = cur.next; cur.next = prev; prev = cur; cur = next; }
    return prev;
}
```

**解题思路：** 快慢指针找到中点 → 反转后半段 → 双指针从两头向中间比较 → 完成比较后可选还原链表。核心：前半段和反转后的后半段逐节点比较。

---

### 翻转链表

#### 206. 反转链表（迭代）

**题设：** 给你链表 `head`，反转链表并返回反转后的链表头。

```csharp
public ListNode ReverseList(ListNode head) {
    ListNode prev = null, cur = head;
    while (cur != null) {
        ListNode next = cur.next;
        cur.next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}
```

**解题思路：** 三指针法。prev 指向已反转部分的头，cur 指向待反转节点。每次循环保存 `cur.next`，将 `cur.next` 指向 `prev`，然后 `prev = cur, cur = next`。最终 prev 即为新链表头。核心口诀：**保存 next、翻转指针、移动指针**。

---

#### 92. 反转链表 II（区间反转）

**题设：** 给你链表的头节点 `head` 和两个整数 `left` 和 `right`（left ≤ right），反转从位置 `left` 到 `right` 的链表节点，返回反转后的链表。

```csharp
public ListNode ReverseBetween(ListNode head, int left, int right) {
    ListNode dummy = new ListNode(0, head), pre = dummy;
    for (int i = 0; i < left - 1; i++) pre = pre.next;
    ListNode cur = pre.next;
    for (int i = 0; i < right - left; i++) {
        ListNode next = cur.next;
        cur.next = next.next;
        next.next = pre.next;
        pre.next = next;
    }
    return dummy.next;
}
```

**解题思路：** 三步走——① 先走 `left-1` 步找到反转区间前一个节点 `pre`；② 用迭代法反转 `[left, right]` 区间（总共反转 `right-left` 次）；③ 将 `pre.next` 接到反转后的链表。dummy 节点处理头结点特殊情况。口诀：**定位→翻转→重连**。

---

#### 25. K 个一组翻转链表（进阶）

**题设：** 给你链表 `head`，每 `k` 个节点一组进行翻转，不足 k 个则保持原样。返回翻转后的链表。

```csharp
public ListNode ReverseKGroup(ListNode head, int k) {
    ListNode dummy = new ListNode(0, head), prev = dummy;
    while (true) {
        ListNode kth = prev;
        for (int i = 0; i < k; i++) { kth = kth.next; if (kth == null) return dummy.next; }
        ListNode next = kth.next;
        (ListNode cur, ListNode nxt) = (prev.next, next);
        for (int i = 0; i < k; i++) {
            ListNode tmp = cur.next;
            cur.next = nxt;
            nxt = cur;
            cur = tmp;
        }
        ListNode last = prev.next;
        prev.next = nxt;
        prev = last;
    }
}
```

**解题思路：** 每次找到当前组的第 k 个节点作为 `kth`，先保存 `kth.next` 作为下一组的起点。然后反转当前组的 k 个节点（迭代法），反转后 `prev.next` 指向新头（原尾），原头（原尾）成为新尾，`prev` 更新到新尾，继续下一轮。

---

### 合并 / 相交

#### 21. 合并两个有序链表

**题设：** 将两个升序链表合并为一个升序链表，返回合并后的链表头。

```csharp
public ListNode MergeTwoLists(ListNode l1, ListNode l2) {
    ListNode dummy = new ListNode(0);
    ListNode cur = dummy;
    while (l1 != null && l2 != null) {
        if (l1.val <= l2.val) { cur.next = l1; l1 = l1.next; }
        else { cur.next = l2; l2 = l2.next; }
        cur = cur.next;
    }
    cur.next = l1 ?? l2;
    return dummy.next;
}
```

**解题思路：** 归并排序的合并步骤。双指针比较两链表当前节点，小的接入结果链表并后移。最终把剩余部分直接接上。Dummy 节点统一头结点处理。**时间 O(n+m)，空间 O(1)**。

---

#### 160. 相交链表

**题设：** 给你两个链表 `headA` 和 `headB`，返回两个链表相交的起始节点。如果不存在相交节点则返回 null。

```csharp
public ListNode GetIntersectionNode(ListNode headA, ListNode headB) {
    ListNode a = headA, b = headB;
    while (a != b) {
        a = a == null ? headB : a.next;
        b = b == null ? headA : b.next;
    }
    return a;
}
```

**解题思路：** 双指针分别从 A、B 出发，走完自己的链表后切换到对方起点。若相交，两者走过的总长度相同 (a + b)，必在交点相遇；若不相交，最终同时到达 null。**数学证明：A走过a+c+B走过b，B走过b+c+A走过a，总长相等**。

---

#### 86. 分隔链表

**题设：** 给你链表 `head` 和一个值 `x`，将小于 `x` 的节点排在大于等于 `x` 的节点之前，保持各自的相对顺序。

```csharp
public ListNode Partition(ListNode head, int x) {
    ListNode before = new ListNode(0), after = new ListNode(0);
    ListNode bCur = before, aCur = after;
    while (head != null) {
        if (head.val < x) { bCur.next = head; bCur = bCur.next; }
        else { aCur.next = head; aCur = aCur.next; }
        head = head.next;
    }
    aCur.next = null;
    bCur.next = after.next;
    return before.next;
}
```

**解题思路：** 用两个 dummy 链表分别收集小于 x 和大于等于 x 的节点，最后拼接。空间 O(1)（只创建了两个头结点），时间 O(n)。

---

#### 328. 奇偶链表

**题设：** 给定单链表，将所有索引为奇数的节点和索引为偶数的节点分别集中在一起，保持相对顺序。索引从 0 开始。

```csharp
public ListNode OddEvenList(ListNode head) {
    if (head == null) return head;
    ListNode odd = head, even = head.next, evenHead = even;
    while (even?.next != null) {
        odd.next = even.next;
        odd = odd.next;
        even.next = odd.next;
        even = even.next;
    }
    odd.next = evenHead;
    return head;
}
```

**解题思路：** 用 odd/even 双指针维护奇链和偶链，evenHead 保存偶链头。最后 `odd.next = evenHead`。核心：在循环内同时维护奇链和偶链的 next 指针，交叉进行。

---

### 链表总结

| 操作 | 关键点 |
|------|--------|
| 快慢指针 | 找中点 `fast?.next?.next`；环检测 `fast?.next` |
| 反转链表 | `cur.next = prev` 三指针迭代 |
| 区间反转 | dummy + 定位 + 头插法 |
| 合并链表 | 双指针比较 + dummy |
| 相交链表 | A走完接B，B走完接A |
| 回文链表 | 快慢找中点 → 反转后半段 → 比较 |

---

## 2. 双指针 (Two Pointers)

#### 15. 三数之和

**题设：** 给你整数数组 `nums`，返回所有满足 `nums[i] + nums[j] + nums[k] == 0` 且 `i < j < k` 的三元组。答案不可重复。

```csharp
public IList<IList<int>> ThreeSum(int[] nums) {
    Array.Sort(nums);
    var res = new List<IList<int>>();
    for (int i = 0; i < nums.Length - 2; i++) {
        if (i > 0 && nums[i] == nums[i-1]) continue;
        int l = i + 1, r = nums.Length - 1;
        while (l < r) {
            int sum = nums[i] + nums[l] + nums[r];
            if (sum == 0) {
                res.Add(new[] { nums[i], nums[l], nums[r] });
                while (l < r && nums[l] == nums[l+1]) l++;
                while (l < r && nums[r] == nums[r-1]) r--;
                l++; r--;
            } else if (sum < 0) l++;
            else r--;
        }
    }
    return res;
}
```

**解题思路：** 先排序固定一个数 `i`，再用双指针找另外两个数（对撞指针）。**去重是关键**：跳过与上次相同的 `i`、相同的 `l`、相同的 `r`，避免输出重复三元组。排序后 `sum < 0` 则左指针右移，`sum > 0` 则右指针左移。

---

#### 11. 盛水容器

**题设：** 给定 `n` 个非负整数 `a1, a2, ..., an`，每个数代表坐标 `(i, ai)` 处的垂线，两条垂线与 x 轴构成容器。求容器能盛的最大水量。

```
输入：height = [1,8,6,2,5,4,8,3,7]
输出：49（8 和 7 之间）
```

```csharp
public int MaxArea(int[] height) {
    int l = 0, r = height.Length - 1, ans = 0;
    while (l < r) {
        int area = Math.Min(height[l], height[r]) * (r - l);
        ans = Math.Max(ans, area);
        if (height[l] < height[r]) l++;
        else r--;
    }
    return ans;
}
```

**解题思路：** 对撞双指针。宽固定为 `r-l`，高度由较短边决定。每次移动**较短边的指针**——因为容量由短板决定，移动长边只会让宽度和高度同时减小或不变，不可能是更优解。

---

#### 42. 接雨水

**题设：** 给定 `n` 个非负整数表示柱状图的高度，计算下雨后能盛多少单位的水。

```
输入：height = [0,1,0,2,1,0,1,3,2,1,2,1]
输出：6
```

```csharp
public int Trap(int[] height) {
    int l = 0, r = height.Length - 1, lMax = 0, rMax = 0, ans = 0;
    while (l < r) {
        if (height[l] < height[r]) {
            lMax = Math.Max(lMax, height[l]);
            ans += lMax - height[l++];
        } else {
            rMax = Math.Max(rMax, height[r]);
            ans += rMax - height[r--];
        }
    }
    return ans;
}
```

**解题思路：** 双指针 + 记录左右最大高度。对于每个位置，能接的雨水 = `min(左边最高, 右边最高) - 当前高度`。从左往右遍历时，`lMax` 已知而 `rMax` 未知，但**能确定的是：如果 `height[l] < height[r]`，则水量由 `height[l]` 决定**（因为右边的 `rMax` 至少是 `height[r]`），此时可以安全结算左侧。反之亦然。

---

#### 167. 两数之和 II

**题设：** 给你一个下标从 1 开始的整数数组 `numbers`，已按非递减顺序排列。找出两数之和等于目标值的两个下标。返回 `[index1, index2]`。

```csharp
public int[] TwoSum(int[] numbers, int target) {
    int l = 0, r = numbers.Length - 1;
    while (l < r) {
        int sum = numbers[l] + numbers[r];
        if (sum == target) return new[] { l + 1, r + 1 };
        else if (sum < target) l++;
        else r--;
    }
    return new[] { -1, -1 };
}
```

**解题思路：** 有序数组的双指针。和大于目标右指针左移，和小于目标左指针右移。注意返回的是 1-indexed 下标。

---

#### 977. 有序数组的平方

**题设：** 给你按非递减顺序排序的整数数组 `nums`，返回每个数的平方组成的新数组，也按非递减顺序排序。要求 O(n)。

```csharp
public int[] SortedSquares(int[] nums) {
    int n = nums.Length, i = 0, j = n - 1, k = n - 1;
    int[] res = new int[n];
    while (i <= j) {
        if (nums[i] * nums[i] > nums[j] * nums[j]) {
            res[k--] = nums[i] * nums[i++];
        } else {
            res[k--] = nums[j] * nums[j--];
        }
    }
    return res;
}
```

**解题思路：** 原数组平方后最大的一定在两端（因为负数平方后也是大的）。用双指针从两端向中间走，每次取两端的较大值放入结果数组尾部。**类似归并排序的合并步骤**。

---

#### 88. 合并两个有序数组

**题设：** 给你两个有序整数数组 `nums1` 和 `nums2`，将 `nums2` 合并到 `nums1` 中，使其成为有序数组。原地修改 `nums1`（m + n 长度）。

```csharp
public void Merge(int[] nums1, int m, int[] nums2, int n) {
    int i = m - 1, j = n - 1, k = m + n - 1;
    while (i >= 0 && j >= 0) {
        nums1[k--] = nums1[i] > nums2[j] ? nums1[i--] : nums2[j--];
    }
    while (j >= 0) nums1[k--] = nums2[j--];
}
```

**解题思路：** 从后往前双指针。`nums1` 末尾是空的，从两数组尾部开始比较，大的放到 `nums1` 的末尾。**从后往前的好处是不需要额外数组，且不会覆盖未处理的数据**。

---

## 3. 滑动窗口 (Sliding Window)

#### 3. 无重复字符的最长子串

**题设：** 给定字符串 `s`，找出其中不包含重复字符的最长子串的长度。

```
输入：s = "abcabcbb"  → 输出：3（"abc"）
输入：s = "bbbbb"     → 输出：1（"b"）
```

```csharp
public int LengthOfLongestSubstring(string s) {
    int[] cnt = new int[256];
    int l = 0, ans = 0;
    for (int r = 0; r < s.Length; r++) {
        cnt[s[r]]++;
        while (cnt[s[r]] > 1) cnt[s[l++]]--;
        ans = Math.Max(ans, r - l + 1);
    }
    return ans;
}
```

**解题思路：** 右指针扩展窗口，左指针收缩窗口。用数组/字典记录字符出现次数。当右指针遇到重复字符（count > 1），左指针持续右移并减少计数，直到重复消除。**核心：右扩、左缩、更新答案**。时间 O(n)，空间 O(1)（字符集有限）。

---

#### 438. 字母异位词

**题设：** 给定字符串 `s` 和 `p`，找出 `s` 中所有 `p` 的字母异位词的起始索引。返回所有满足条件的索引列表。

```
输入：s = "cbaebabacd", p = "abc"  → 输出：[0, 6]（"cba"和"bac"）
```

```csharp
public IList<int> FindAnagrams(string s, string p) {
    int[] need = new int[256], cur = new int[256];
    foreach (char c in p) need[c]++;
    var res = new List<int>();
    for (int r = 0, l = 0; r < s.Length; r++) {
        cur[s[r]]++;
        if (r - l + 1 > p.Length) cur[s[l++]]--;
        if (r - l + 1 == p.Length && need.SequenceEqual(cur))
            res.Add(l);
    }
    return res;
}
```

**解题思路：** 固定大小的滑动窗口 + 计数数组比较。先统计模式串 `p` 中各字符出现次数作为 `need`，然后在 `s` 上滑动窗口，用 `cur` 记录窗口内字符次数。每当窗口大小等于 `p.Length`，比较 `need` 和 `cur` 是否相等。窗口右移时，移出的字符计数减一。

---

#### 76. 最小覆盖子串（困难）

**题设：** 给你字符串 `s` 和 `t`，返回 `s` 中包含 `t` 所有字符的最小子串。若不存在返回空字符串。

```
输入：s = "ADOBECODEBANC", t = "ABC"  → 输出："BANC"
```

```csharp
public string MinWindow(string s, string t) {
    int[] need = new int[256], cur = new int[256];
    foreach (char c in t) need[c]++;
    int count = 0, l = 0, minLen = int.MaxValue, minL = 0;
    for (int r = 0; r < s.Length; r++) {
        if (++cur[s[r]] <= need[s[r]]) count++;
        while (count == t.Length) {
            if (r - l + 1 < minLen) { minLen = r - l + 1; minL = l; }
            if (--cur[s[l]] < need[s[l++]]) count--;
        }
    }
    return minLen == int.MaxValue ? "" : s.Substring(minL, minLen);
}
```

**解题思路：** 变长滑动窗口。先扩大右端包含所有必要字符，再用左端收缩寻找最小窗口。`need` 记录需要的字符及其数量，`count` 记录当前已满足的字符种类数（当 count == t.Length 时窗口有效）。

---

#### 567. 字符串的排列

**题设：** 给定字符串 `s1` 和 `s2`，判断 `s2` 是否包含 `s1` 的排列（即 `s2` 的某个子串是 `s1` 的全排列）。返回 true/false。

```csharp
public bool CheckInclusion(string s1, string s2) {
    int[] need = new int[256], cur = new int[256];
    foreach (char c in s1) need[c]++;
    for (int r = 0, l = 0; r < s2.Length; r++) {
        cur[s2[r]]++;
        if (r - l + 1 > s1.Length) cur[s2[l++]]--;
        if (r - l + 1 == s1.Length && need.SequenceEqual(cur))
            return true;
    }
    return false;
}
```

**解题思路：** 与 438 类似，只是判断条件变成"两数组相等时直接返回 true"。长度固定的滑动窗口。

---

## 4. 二叉树遍历 (DFS / BFS)

### DFS 模板

#### 144. 前序遍历

**题设：** 给你二叉树根节点 `root`，返回前序遍历结果（根 → 左 → 右）。

```csharp
public IList<int> PreorderTraversal(TreeNode root) {
    var res = new List<int>();
    void dfs(TreeNode node) {
        if (node == null) return;
        res.Add(node.val);
        dfs(node.left);
        dfs(node.right);
    }
    dfs(root);
    return res;
}
```

**解题思路：** 根→左→右的顺序递归访问。先把当前节点值加入结果，再递归左右子树。递归模板：**终止条件 + 访问当前 + 递归左右**。中序和后序只需调整 `res.Add` 的位置。

---

#### 104. 二叉树最大深度

**题设：** 给你二叉树根节点，返回其最大深度（从根到最深叶子节点的节点数）。

```csharp
public int MaxDepth(TreeNode root) {
    if (root == null) return 0;
    return 1 + Math.Max(MaxDepth(root.left), MaxDepth(root.right));
}
```

**解题思路：** 递归的返回值即为深度。后递归计算左右子树的深度，取较大者加一（加上当前节点层）。**后序位置收集信息 + 自底向上返回**，这是树形 DP 的基础模式。

---

#### 110. 平衡二叉树

**题设：** 给你二叉树根节点，判断它是否是高度平衡的（二叉树中每个节点的左右子树高度差不超过 1）。

```csharp
public bool IsBalanced(TreeNode root) {
    bool valid = true;
    Dfs(root);
    return valid;
    int Dfs(TreeNode node) {
        if (node == null) return 0;
        int l = Dfs(node.left), r = Dfs(node.right);
        if (Math.Abs(l - r) > 1) valid = false;
        return Math.Max(l, r) + 1;
    }
}
```

**解题思路：** 递归计算每个子树的高度，在计算过程中判断是否平衡。**关键：后序遍历**——先计算子树高度，再判断子树是否平衡并返回自身高度。如果发现不平衡（高度差>1），设置 `valid = false` 但不提前返回（要让递归全部走完）。

---

#### 543. 二叉树直径

**题设：** 给你二叉树根节点，返回任意两个节点之间的最长路径长度（经过的边数）。

```csharp
int ans = 0;
public int DiameterOfBinaryTree(TreeNode root) {
    Dfs(root);
    return ans;
    int Dfs(TreeNode node) {
        if (node == null) return 0;
        int l = Dfs(node.left), r = Dfs(node.right);
        ans = Math.Max(ans, l + r);
        return Math.Max(l, r) + 1;
    }
}
```

**解题思路：** 类似平衡二叉树，在后序递归中计算经过当前节点的最长路径 = `左子树深度 + 右子树深度`。维护全局 `ans` 记录最大直径。**注意：直径不一定经过根节点**。返回值为该节点的深度（用于父节点计算）。

---

#### 226. 翻转二叉树

**题设：** 给你二叉树根节点，翻转这棵二叉树并返回新的根节点。

```csharp
public TreeNode InvertTree(TreeNode root) {
    if (root == null) return root;
    (root.left, root.right) = (InvertTree(root.right), InvertTree(root.left));
    return root;
}
```

**解题思路：** 递归交换左右子节点，然后递归处理子树。先递归翻转左右子树，再交换左右指针。**也可以用 BFS 逐层交换**。

---

#### 101. 对称二叉树

**题设：** 给你二叉树根节点，检查它是否是镜像对称的。

```csharp
public bool IsSymmetric(TreeNode root) => IsMirror(root.left, root.right);
bool IsMirror(TreeNode l, TreeNode r) {
    if (l == null || r == null) return l == r;
    return l.val == r.val && IsMirror(l.left, r.right) && IsMirror(l.right, r.left);
}
```

**解题思路：** 递归比较左子树和右子树。左子树的左和右子树的右镜像比较，左子树的右和右子树的左镜像比较。**双递归：一个处理左，一个处理右**。

---

#### 112. 路径总和

**题设：** 给你二叉树根节点和一个整数 `targetSum`。判断是否存在从根到叶子节点的路径上所有节点值之和等于 `targetSum`。

```csharp
public bool HasPathSum(TreeNode root, int targetSum) {
    if (root == null) return false;
    if (root.left == null && root.right == null) return targetSum == root.val;
    return HasPathSum(root.left, targetSum - root.val)
        || HasPathSum(root.right, targetSum - root.val);
}
```

**解题思路：** 从根节点出发，每向下走一步就从目标和中减去当前节点值。到达叶子节点时判断 `targetSum == 0`。**前序位置做减法，叶子位置做判断**。

---

#### 437. 路径总和 III（节点值可正可负）

**题设：** 给你二叉树根节点和一个整数 `targetSum`。返回路径和等于 `targetSum` 的路径数目。路径方向必须向子节点延伸，但不必须从根节点开始。

```csharp
int ans = 0;
public int PathSum(TreeNode root, int targetSum) {
    if (root == null) return 0;
    Dfs(root, targetSum);
    PathSum(root.left, targetSum);
    PathSum(root.right, targetSum);
    return ans;
}
void Dfs(TreeNode node, long cur) {
    if (node == null) return;
    cur += node.val;
    if (cur == targetSum) ans++;
    Dfs(node.left, cur);
    Dfs(node.right, cur);
}
```

**解题思路：** 以每个节点为起点的路径需要单独 DFS（因为路径不一定从根开始）。前缀和思想：用字典记录从根到当前节点的路径上各前缀和出现的次数，检差即可。**注意用 long 防止溢出**。

---

### BFS 模板（层序遍历）

#### 102. 二叉树层序遍历

**题设：** 给你二叉树根节点，按层返回节点值（每层一行）。

```csharp
public IList<IList<int>> LevelOrder(TreeNode root) {
    var res = new List<IList<int>>();
    if (root == null) return res;
    var q = new Queue<TreeNode>();
    q.Enqueue(root);
    while (q.Count > 0) {
        int cnt = q.Count;
        var level = new List<int>();
        for (int i = 0; i < cnt; i++) {
            var node = q.Dequeue();
            level.Add(node.val);
            if (node.left != null) q.Enqueue(node.left);
            if (node.right != null) q.Enqueue(node.right);
        }
        res.Add(level);
    }
    return res;
}
```

**解题思路：** 用队列（BFS）按层遍历。每轮处理当前队列中所有节点（`q.Count` 即为本层节点数），弹出所有节点加入本层列表，同时把它们的子节点入队。**分层的关键：先记录 `cnt = q.Count`，然后用 for 循环固定处理本层数量**。

---

#### 199. 二叉树的右视图

**题设：** 给你二叉树根节点，想象你站在它的右边，返回你能看到的节点值（从上到下）。

```csharp
public IList<int> RightSideView(TreeNode root) {
    var res = new List<int>();
    if (root == null) return res;
    var q = new Queue<TreeNode>();
    q.Enqueue(root);
    while (q.Count > 0) {
        int cnt = q.Count;
        for (int i = 0; i < cnt; i++) {
            var node = q.Dequeue();
            if (i == cnt - 1) res.Add(node.val);
            if (node.left != null) q.Enqueue(node.left);
            if (node.right != null) q.Enqueue(node.right);
        }
    }
    return res;
}
```

**解题思路：** BFS 层序遍历，每层取最后一个节点（即队列中当前层的最后一个元素）加入结果。**也可以用 DFS（先右后左，保证每层第一个被访问的就是右视图节点）**。

---

#### 222. 完全二叉树的节点数

**题设：** 给你一个完全二叉树的根节点，求其节点总数。要求时间复杂度 O(log² N)。

```csharp
public int CountNodes(TreeNode root) {
    if (root == null) return 0;
    int lDepth = 0, rDepth = 0;
    TreeNode l = root.left, r = root.right;
    while (l != null) { lDepth++; l = l.left; }
    while (r != null) { rDepth++; r = r.right; }
    if (lDepth == rDepth) return (1 << (lDepth + 1)) - 1;
    return 1 + CountNodes(root.left) + CountNodes(root.right);
}
```

**解题思路：** 完全二叉树的性质：若左右深度相同，则该子树是满二叉树（节点数 = 2^h - 1）；否则递归左右子树。利用满二叉树的节点数公式加速，从 O(N) 优化到 O(log² N)。

---

### 二叉搜索树（BST）

#### 98. 验证 BST

**题设：** 给你二叉树根节点，判断它是否是一棵有效的二叉搜索树（BST）。

```csharp
long pre = long.MinValue;
public bool IsValidBST(TreeNode root) {
    if (root == null) return true;
    if (!IsValidBST(root.left)) return false;
    if (root.val <= pre) return false;
    pre = root.val;
    return IsValidBST(root.right);
}
```

**解题思路：** BST 的中序遍历结果是一个严格递增序列。利用这一性质，在中序遍历过程中维护一个 `pre` 变量记录上一个节点的值，只需检查 `root.val > pre` 即可。注意用 `long` 类型防止 int 溢出。

---

#### 700. BST 搜索

**题设：** 在 BST 中搜索值为 `val` 的节点，返回以该节点为根的子树。若不存在返回 null。

```csharp
public TreeNode SearchBST(TreeNode root, int val) {
    if (root == null || root.val == val) return root;
    return val < root.val ? SearchBST(root.left, val) : SearchBST(root.right, val);
}
```

**解题思路：** 利用 BST 的有序性：目标值小于当前节点往左搜，大于往右搜。递归版和迭代版均可，时间复杂度 O(h)，h 为树高，最坏 O(n)。

---

#### 450. 删除 BST 节点

**题设：** 给定 BST 的根节点和 key，删除值为 key 的节点并返回新的根节点。

```csharp
public TreeNode DeleteNode(TreeNode root, int key) {
    if (root == null) return null;
    if (key < root.val) root.left = DeleteNode(root.left, key);
    else if (key > root.val) root.right = DeleteNode(root.right, key);
    else {
        if (root.left == null) return root.right;
        if (root.right == null) return root.left;
        TreeNode minNode = root.right;
        while (minNode.left != null) minNode = minNode.left;
        root.val = minNode.val;
        root.right = DeleteNode(root.right, root.val);
    }
    return root;
}
```

**解题思路：** 找到目标节点后分三种情况：① 无左子树 → 返回右子树；② 无右子树 → 返回左子树；③ 左右子树都有 → 在右子树中找最小节点（后继）替代当前值，然后递归删除右子树中的该最小节点。

---

### 二叉树总结

| 题型 | 核心思路 |
|------|----------|
| 前/中/后序遍历 | 递归 + res.Add 位置决定顺序 |
| 最大深度 | 后序返回 max(left, right) + 1 |
| 平衡二叉树 | 后序算高度 + 判断差值 |
| 直径 | 后序算深度 + 更新 ans = l + r |
| 验证 BST | 中序遍历递增 |
| 路径总和 | 前序减法 + 叶子节点判断 |
| 层序遍历 | BFS + `cnt = q.Count` 分层 |
| 完全二叉树节点数 | 满二叉树加速：左右深度相同则 2^h-1 |

---

## 5. 动态规划 (DP)

### 选或不选（0/1 背包）

#### 416. 分割等和子集

**题设：** 给你一个只包含正整数的非空数组 `nums`，判断是否可以将数组分成两个元素和相等的子集。

```csharp
public bool CanPartition(int[] nums) {
    int sum = nums.Sum();
    if (sum % 2 == 1) return false;
    int target = sum / 2;
    bool[] dp = new bool[target + 1];
    dp[0] = true;
    foreach (int w in nums) {
        for (int j = target; j >= w; j--) dp[j] = dp[j] || dp[j - w];
    }
    return dp[target];
}
```

**解题思路：** 转化为"能否从数组中选出若干数使和为 target"的 0/1 背包问题。`dp[j]` 表示能否凑出和 j。**倒序遍历**物品确保每个物品只选一次。对于每个数 `w`，更新 `dp[j] = dp[j] || dp[j-w]`。最终返回 `dp[target]`。

---

#### 494. 目标和

**题设：** 给你整数数组 `nums` 和目标整数 `target`。在每个数前添加 `+` 或 `-`，使运算结果等于 `target`，返回共有多少种组合方式。

```csharp
public int FindTargetSumWays(int[] nums, int target) {
    int sum = nums.Sum();
    if (Math.Abs(target) > sum) return 0;
    int[,] dp = new int[nums.Length + 1, sum * 2 + 1];
    dp[0, sum] = 1;
    for (int i = 1; i <= nums.Length; i++) {
        for (int j = 0; j <= sum * 2; j++) {
            int v = nums[i-1];
            if (j - v >= 0) dp[i, j] += dp[i-1, j - v];
            if (j + v < 2 * sum + 1) dp[i, j] += dp[i-1, j + v];
        }
    }
    return dp[nums.Length, target + sum];
}
```

**解题思路：** 转化为正负号分配问题：`+` 数的和为 P，`-` 数的和为 N，则 `P - N = target`，且 `P + N = sum`。所以 `P = (sum + target) / 2`。用 0/1 背包计数：每个数选或不选使和为 P。`dp[i,j]` = 用前 i 个数凑出和 j 的方法数。

---

#### 474. 一和零（0/1 背包二维）

**题设：** 给你字符串数组 `strs`，每个字符串由 `0` 和 `1` 组成。你有 `m` 个 `0` 和 `n` 个 `1`，返回最多能选出多少个字符串使得使用的 `0` 和 `1` 总数不超过限制。

```csharp
public int FindMaxForm(string[] strs, int m, int n) {
    int[,] dp = new int[m + 1, n + 1];
    foreach (string s in strs) {
        int cnt0 = s.Count(c => c == '0'), cnt1 = s.Length - cnt0;
        for (int i = m; i >= cnt0; i--)
            for (int j = n; j >= cnt1; j--)
                dp[i, j] = Math.Max(dp[i, j], dp[i - cnt0, j - cnt1] + 1);
    }
    return dp[m, n];
}
```

**解题思路：** 二维 0/1 背包，`dp[i][j]` = 使用 i 个 0 和 j 个 1 能选的最大字符串数。物品是每个字符串，其"重量"是两个维度（0 的数量和 1 的数量）。二维倒序遍历。

---

### 路径问题

#### 62. 不同路径

**题设：** 一个机器人位于 `m x n` 网格的左上角，只能向下或向右移动。问有多少种不同的路径可以到达右下角？

```
输入：m=3, n=7  → 输出：28
```

```csharp
public int UniquePaths(int m, int n) {
    int[] dp = new int[n];
    Array.Fill(dp, 1);
    for (int i = 1; i < m; i++)
        for (int j = 1; j < n; j++)
            dp[j] += dp[j-1];
    return dp[n-1];
}
```

**解题思路：** 机器人只能往下和往右走，到达每个格子的路径数 = 上边格子路径数 + 左边格子路径数。一维 DP：`dp[j]` 表示当前行的第 j 列路径数。由于 `dp[j]` 在更新前存储的是上一行的值，加上 `dp[j-1]`（当前行左边的值）即为当前位置的路径数。

---

#### 64. 最小路径和

**题设：** 给定 `m x n` 网格 `grid`，每格有非负权重。只能向下或向右走，返回路径（从左上到右下）的最小权重和。

```csharp
public int MinPathSum(int[][] grid) {
    int m = grid.Length, n = grid[0].Length;
    int[] dp = new int[n];
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            if (i == 0 && j == 0) dp[j] = grid[i][j];
            else if (i == 0) dp[j] += grid[i][j];
            else if (j == 0) dp[j] = grid[i][j] + dp[j];
            else dp[j] = grid[i][j] + Math.Min(dp[j], dp[j-1]);
        }
    }
    return dp[n-1];
}
```

**解题思路：** 每个格子只能从上或左走来，`dp[j]` 更新时 `dp[j]` 是上一行同列的最小路径，`dp[j-1]` 是当前行左边格子的最小路径。取两者较小值加上当前格子值。第一行和第一列分别只有一条路径，注意单独处理边界。

---

#### 5. 最长回文子串（经典）

**题设：** 给你字符串 `s`，返回其中最长的回文子串。

```
输入：s = "babad"  → 输出："bab" 或 "aba"
```

```csharp
public string LongestPalindrome(string s) {
    int n = s.Length, start = 0, maxLen = 1;
    bool[,] dp = new bool[n, n];
    for (int i = 0; i < n; i++) dp[i, i] = true;
    for (int len = 2; len <= n; len++) {
        for (int i = 0; i + len <= n; i++) {
            int j = i + len - 1;
            if (len == 2) dp[i, j] = s[i] == s[j];
            else dp[i, j] = (s[i] == s[j]) && dp[i + 1, j - 1];
            if (dp[i, j] && len > maxLen) { maxLen = len; start = i; }
        }
    }
    return s.Substring(start, maxLen);
}
```

**解题思路：** `dp[i][j]` = s[i..j] 是否为回文。若 `s[i]==s[j]` 且 `dp[i+1][j-1]` 为真（或 len<=2），则为回文。按长度从小到大枚举（因为 dp[i+1][j-1] 是子问题）。空间 O(n²)，时间 O(n²)。**中心扩展法 O(n) 更优**。

---

#### 516. 最长回文子序列

**题设：** 给你字符串 `s`，找出其中最长的回文子序列的长度。子序列不要求连续。

```csharp
public int LongestPalindromeSubseq(string s) {
    int n = s.Length;
    int[,] dp = new int[n, n];
    for (int i = n - 1; i >= 0; i--) {
        dp[i, i] = 1;
        for (int j = i + 1; j < n; j++) {
            if (s[i] == s[j]) dp[i, j] = dp[i + 1, j - 1] + 2;
            else dp[i, j] = Math.Max(dp[i + 1, j], dp[i, j - 1]);
        }
    }
    return dp[0, n - 1];
}
```

**解题思路：** `dp[i][j]` = s[i..j] 的最长回文子序列长度。若两端相同则 `dp[i+1][j-1] + 2`；否则取 `max(dp[i+1][j], dp[i][j-1])`。**倒序遍历 i（保证 dp[i+1] 已知），正序遍历 j**。

---

#### 221. 最大正方形

**题设：** 在二维二进制矩阵中找出只包含 `1` 的最大正方形面积。

```csharp
public int MaximalSquare(char[][] matrix) {
    int m = matrix.Length, n = matrix[0].Length, max = 0;
    int[,] dp = new int[m, n];
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            if (matrix[i][j] == '1') {
                if (i == 0 || j == 0) dp[i, j] = 1;
                else dp[i, j] = Math.Min(Math.Min(dp[i-1, j], dp[i, j-1]), dp[i-1, j-1]) + 1;
                max = Math.Max(max, dp[i, j]);
            }
        }
    }
    return max * max;
}
```

**解题思路：** `dp[i][j]` = 以 `(i,j)` 为右下角的最大正方形边长。若 `matrix[i][j]=='1'`，则 `dp[i][j] = min(dp[i-1,j], dp[i,j-1], dp[i-1,j-1]) + 1`。**取三个方向最小 + 1，因为正方形取决于最短边**。

---

### 股票买卖系列

#### 121. 买卖股票（只能一次）

**题设：** 你只能有一天持有股票（买入前不能已持有），求最大利润。

```csharp
public int MaxProfit(int[] prices) {
    int minPrice = int.MaxValue, maxProfit = 0;
    foreach (int p in prices) {
        maxProfit = Math.Max(maxProfit, p - minPrice);
        minPrice = Math.Min(minPrice, p);
    }
    return maxProfit;
}
```

**解题思路：** 维护最低价格和最大利润。遍历过程中，`maxProfit = max(maxProfit, price - minPrice)`，同时更新最低价格。**一句话：在最低点买入，在最高点卖出（但实际求的是全局最大差值）**。

---

#### 122. 买卖股票（无限次）

**题设：** 你可以无限次交易（买入前必须先卖出），求最大利润。

```csharp
public int MaxProfit2(int[] prices) {
    int profit = 0;
    for (int i = 1; i < prices.Length; i++)
        if (prices[i] > prices[i-1])
            profit += prices[i] - prices[i-1];
    return profit;
}
```

**解题思路：** 只要相邻两天价格上升，就在前一天买入当天卖出（累加利润）。这等价于把整个上升段拆分成了若干小区间。贪心证明：跨越多天的上升利润 = 各相邻天利润之和。

---

#### 123. 买卖股票（最多两次）

**题设：** 你最多完成两笔交易（买入前必须先卖出，两笔交易不可重叠），求最大利润。

```csharp
public int MaxProfit3(int[] prices) {
    int k = 2, n = prices.Length;
    int[,,] dp = new int[n, k + 1, 2];
    for (int i = 0; i < n; i++)
        for (int t = 1; t <= k; t++) {
            if (i == 0) { dp[i, t, 1] = -prices[0]; continue; }
            dp[i, t, 0] = Math.Max(dp[i-1, t, 0], dp[i-1, t, 1] + prices[i]);
            dp[i, t, 1] = Math.Max(dp[i-1, t, 1], dp[i-1, t-1, 0] - prices[i]);
        }
    return dp[n-1, k, 0];
}
```

**解题思路：** 状态机 DP。三维 dp `[day][k+1][2]`，2 表示持有/不持有状态。`dp[i][t][0] = max(昨天不持有, 今天卖出)`，`dp[i][t][1] = max(昨天持有, 今天买入)`。第 t 次交易的状态由第 t-1 次交易转移而来。

---

#### 152. 乘积最大子数组

**题设：** 给你整数数组 `nums`，找出其中乘积最大的连续子数组（子数组最少包含一个元素），返回其乘积。

```csharp
public int MaxProduct(int[] nums) {
    int max = nums[0], min = nums[0], ans = nums[0];
    for (int i = 1; i < nums.Length; i++) {
        int mx = max, mn = min;
        max = Math.Max(nums[i], Math.Max(mx * nums[i], mn * nums[i]));
        min = Math.Min(nums[i], Math.Min(mx * nums[i], mn * nums[i]));
        ans = Math.Max(ans, max);
    }
    return ans;
}
```

**解题思路：** 乘积有负负得正的特性，需要同时维护最大和最小值（因为负数会让最大变最小）。当前最大 = max(自身, 前最大*自身, 前最小*自身)，当前最小同理。**O(n) 时间 O(1) 空间**。

---

### 子序列 / 字符串 DP

#### 300. 最长递增子序列（LIS）

**题设：** 给你整数数组 `nums`，找出其中最长递增子序列的长度（子序列不要求连续）。

```csharp
public int LengthOfLIS(int[] nums) {
    int[] tails = new int[nums.Length];
    int len = 0;
    foreach (int x in nums) {
        int i = Array.BinarySearch(tails, 0, len, x);
        if (i < 0) i = -(i + 1);
        tails[i] = x;
        if (i == len) len++;
    }
    return len;
}
```

**解题思路：** 维护一个递增序列 `tails`，`tails[len]` 表示长度为 len+1 的递增子序列的最小尾部值。对每个数用二分查找找到它在 `tails` 中的位置（第一个 >= 它的位置），更新 `tails`。最终 `tails` 长度即为 LIS 长度。**时间 O(n log n)**。

---

#### 1143. 最长公共子序列（LCS）

**题设：** 给定两个字符串 `text1` 和 `text2`，返回它们的最长公共子序列长度。

```csharp
public int LongestCommonSubsequence(string text1, string text2) {
    int m = text1.Length, n = text2.Length;
    int[,] dp = new int[m + 1, n + 1];
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++)
            dp[i, j] = text1[i-1] == text2[j-1]
                ? dp[i-1, j-1] + 1
                : Math.Max(dp[i-1, j], dp[i, j-1]);
    return dp[m, n];
}
```

**解题思路：** `dp[i][j]` = text1 前 i 个字符与 text2 前 j 个字符的 LCS 长度。若 `text1[i-1] == text2[j-1]`，则 `dp[i][j] = dp[i-1][j-1] + 1`；否则 `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`。**核心：从末尾考虑，相同则共同匹配，否则各退一步求最大**。

---

#### 718. 最长重复子数组

**题设：** 给你两个整数数组 `A` 和 `B`，返回最长重复子数组的长度（子数组必须连续）。

```csharp
public int FindLength(int[] A, int[] B) {
    int m = A.Length, n = B.Length, ans = 0;
    int[,] dp = new int[m + 1, n + 1];
    for (int i = m - 1; i >= 0; i--)
        for (int j = n - 1; j >= 0; j--) {
            dp[i, j] = A[i] == B[j] ? dp[i + 1, j + 1] + 1 : 0;
            ans = Math.Max(ans, dp[i, j]);
        }
    return ans;
}
```

**解题思路：** `dp[i][j]` = A[i:] 和 B[j:] 的最长公共前缀。**倒序遍历确保 dp[i+1][j+1] 已计算**。当 A[i]==B[j] 时 `dp[i][j] = dp[i+1][j+1] + 1`，否则为 0。可用滑动窗口 O((m+n)*min(m,n)) 优化。

---

#### 72. 编辑距离

**题设：** 给你两个单词 `word1` 和 `word2`，可以对 word1 进行三种操作（插入、删除、替换），返回将 word1 变成 word2 的最少操作次数。

```csharp
public int MinDistance(string word1, string word2) {
    int m = word1.Length, n = word2.Length;
    int[,] dp = new int[m + 1, n + 1];
    for (int i = 0; i <= m; i++) dp[i, 0] = i;
    for (int j = 0; j <= n; j++) dp[0, j] = j;
    for (int i = 1; i <= m; i++)
        for (int j = 1; j <= n; j++)
            if (word1[i-1] == word2[j-1]) dp[i, j] = dp[i-1, j-1];
            else dp[i, j] = 1 + Math.Min(dp[i-1, j-1], Math.Min(dp[i-1, j], dp[i, j-1]));
    return dp[m, n];
}
```

**解题思路：** `dp[i][j]` = word1 前 i 个字符变成 word2 前 j 个字符的最少操作数。初始化：删除 i 个字符变为空串 = i，插入 j 个字符 = j。转移：字符相同则不动 `dp[i-1][j-1]`；不同则取 `min(删除, 插入, 替换) + 1`。**替换 = 删掉 i,j 各退一步后替换一个。**

---

### 拆数 / 打家劫舍

#### 198. 打家劫舍

**题设：** 给你整数数组 `nums`，不能偷连续的两间房，返回能偷到的最大金额。

```csharp
public int Rob(int[] nums) {
    int prev2 = 0, prev1 = 0;
    foreach (int n in nums) {
        int cur = Math.Max(prev1, prev2 + n);
        prev2 = prev1; prev1 = cur;
    }
    return prev1;
}
```

**解题思路：** 每间房选或不选，但选了就不能选相邻的。`dp[i]` = 前 i 间房能偷到的最大值。对于第 i 间：偷 = `dp[i-2] + nums[i]`，不偷 = `dp[i-1]`。空间优化：只保留前两个状态 `prev2, prev1`。

---

#### 322. 零钱兑换

**题设：** 给你不同面值的硬币数组 `coins` 和总金额 `amount`，返回凑成总金额所需的最少硬币数。如果无法凑成返回 -1。每种硬币可无限使用。

```csharp
public int CoinChange(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    Array.Fill(dp, amount + 1);
    dp[0] = 0;
    foreach (int c in coins)
        for (int j = c; j <= amount; j++)
            dp[j] = Math.Min(dp[j], dp[j - c] + 1);
    return dp[amount] > amount ? -1 : dp[amount];
}
```

**解题思路：** 完全背包问题，硬币可重复使用。`dp[j]` = 凑成金额 j 的最少硬币数。初始化 `dp[0]=0`，其余为 `amount+1`（表示不可达）。遍历每个硬币，再正序遍历金额 `j`（正序保证重复使用），`dp[j] = min(dp[j], dp[j-c]+1)`。

---

#### 139. 单词拆分

**题设：** 给你字符串 `s` 和一个字符串列表 `wordDict`，判断 `s` 能否被空格拆分成字典中的一个或多个单词。

```csharp
public bool WordBreak(string s, IList<string> wordDict) {
    var set = new HashSet<string>(wordDict);
    int n = s.Length;
    bool[] dp = new bool[n + 1];
    dp[0] = true;
    for (int i = 1; i <= n; i++) {
        for (int j = 0; j < i; j++) {
            if (dp[j] && set.Contains(s.Substring(j, i - j))) {
                dp[i] = true;
                break;
            }
        }
    }
    return dp[n];
}
```

**解题思路：** `dp[i]` = s[0..i) 能否被拆分。枚举上一个切分点 j：`dp[i] = dp[j] && s[j..i) in dict`。类似完全背包的思路，每个字典词作为一个"物品"。

---

### DP 总结：核心状态转移公式速查

| 题目 | 状态定义 | 转移方程 |
|------|----------|----------|
| 416 分割等和 | dp[j]=能否凑j | dp[j] \|\| dp[j-w] |
| 62 路径数 | dp[j]=第i行j列路径数 | dp[j] + dp[j-1] |
| 64 最小路径和 | dp[j]=最小路径和 | grid + min(dp[j], dp[j-1]) |
| 121 股票 | minPrice/maxProfit | maxProfit = max(profit, price-minPrice) |
| 152 乘积最大 | max/min=当前最值 | max = max(自身, mx*自身, mn*自身) |
| 300 LIS | tails[len]=最小尾部 | BinarySearch + 替换/追加 |
| LCS | dp[i][j]=LCS长度 | 相等=dp+1;不等=max(左,上) |
| 72 编辑距离 | dp[i][j]=最少操作 | 相同=dp;不等=1+min(删,插,替) |
| 198 打家劫舍 | prev1/prev2=状态 | max(prev1, prev2+n) |
| 322 零钱兑换 | dp[j]=最少硬币 | min(dp[j], dp[j-c]+1) |

---

## 6. 贪心 (Greedy)

#### 55. 跳跃游戏

**题设：** 给你一个非负整数数组 `nums`，初始位置在索引 0。每个位置的元素表示从该位置最多能跳几步。判断能否到达最后一个索引。

```csharp
public bool CanJump(int[] nums) {
    int reach = 0;
    for (int i = 0; i < nums.Length; i++) {
        if (i > reach) return false;
        reach = Math.Max(reach, i + nums[i]);
    }
    return true;
}
```

**解题思路：** 维护一个 `reach` 表示当前能跳到的最远距离。遍历每个位置，如果当前索引超过 `reach` 则说明无法到达返回 false。每次更新 `reach = max(reach, i + nums[i])`。**关键洞察：不需要具体方案，只需要知道能不能走到终点**。

---

#### 45. 跳跃游戏 II

**题设：** 同上，但要求返回到达最后一个索引的最少跳跃次数。假设一定能够到达。

```csharp
public int Jump(int[] nums) {
    int ans = 0, end = 0, farthest = 0;
    for (int i = 0; i < nums.Length - 1; i++) {
        farthest = Math.Max(farthest, i + nums[i]);
        if (i == end) { ans++; end = farthest; }
    }
    return ans;
}
```

**解题思路：** 在 `CanJump` 的基础上维护 `end`（上一次跳的覆盖范围边界）和 `farthest`（本次跳能达到的最远位置）。当遍历到 `end` 时，说明需要再跳一次，并用 `farthest` 更新新的 `end`。**贪心证明：在每一步都选择在当前覆盖范围内能跳到最远的那一步，使得跳数最少**。

---

#### 435. 无重叠区间

**题设：** 给定一个区间的集合，找到需要移除的最少区间数量，使得剩余区间互不重叠（假设区间端点相同也算重叠）。

```csharp
public int EraseOverlapIntervals(int[][] intervals) {
    Array.Sort(intervals, (a, b) => a[1].CompareTo(b[1]));
    int count = 0, end = int.MinValue;
    foreach (var interval in intervals) {
        if (interval[0] >= end) end = interval[1];
        else count++;
    }
    return count;
}
```

**解题思路：** 按结束时间排序，贪心选择结束最早的区间。维护上一个保留区间的结束时间 `end`，遍历时若当前区间起点 >= `end` 则不重叠可保留，更新 `end`；否则重叠计数加一（需删除）。**按结束时间排序 + 选不重叠的**，使得删除数量最少。

---

#### 452. 用最少的箭引爆气球

**题设：** 一维坐标上有多个气球，给每个气球在 x 轴上对应一个区间 (起点, 终点)。一支箭可以射爆起点和终点都在区间内的所有气球。求最少需要多少支箭。

```csharp
public int FindMinArrowShots(int[][] points) {
    if (points.Length == 0) return 0;
    Array.Sort(points, (a, b) => a[1].CompareTo(b[1]));
    int arrows = 1, end = points[0][1];
    foreach (var p in points) {
        if (p[0] > end) { arrows++; end = p[1]; }
    }
    return arrows;
}
```

**解题思路：** 按结束位置排序，贪心选择弓箭。第一支箭射在第一个气球的结束位置 `end`。遍历气球：若气球起点 > `end` 则需要新的一支箭（`arrows++`，更新 `end` 为当前气球的结束位置）。**本质：找重叠区间数量，不同于 435 的是边界可重叠（闭区间），不相交才需新箭**。

---

#### 56. 合并区间

**题设：** 给定若干区间，将所有重叠的区间合并后返回。

```csharp
public int[][] Merge(int[][] intervals) {
    Array.Sort(intervals, (a, b) => a[0].CompareTo(b[0]));
    var res = new List<int[]>();
    int l = intervals[0][0], r = intervals[0][1];
    for (int i = 1; i < intervals.Length; i++) {
        if (intervals[i][0] <= r) r = Math.Max(r, intervals[i][1]);
        else { res.Add(new[] { l, r }); l = intervals[i][0]; r = intervals[i][1]; }
    }
    res.Add(new[] { l, r });
    return res.ToArray();
}
```

**解题思路：** 按起点排序，贪心合并。维护当前合并区间的 `[l, r]`，若下一个区间起点 <= r 则合并（取 max(r)）；否则保存当前区间，开辟新区间。

---

#### 763. 划分字母区间

**题设：** 将字符串 `s` 划分为尽可能多的片段，每个字母最多出现在一个片段中。返回一个表示每个片段长度的列表。

```csharp
public IList<int> PartitionLabels(string s) {
    int[] last = new int[26];
    for (int i = 0; i < s.Length; i++) last[s[i] - 'a'] = i;
    int anchor = 0, end = 0;
    var res = new List<int>();
    for (int i = 0; i < s.Length; i++) {
        end = Math.Max(end, last[s[i] - 'a']);
        if (i == end) { res.Add(i - anchor + 1); anchor = i + 1; }
    }
    return res;
}
```

**解题思路：** 先统计每个字符最后出现的位置。当遍历到当前位置等于该字符的最远出现位置时，说明一个片段已完整（因为之后不再出现该片段中的任何字符）。

---

## 7. 图论 (BFS / DFS on Graph)

### 岛屿问题

#### 200. 岛屿数量

**题设：** 给你一个由 `'1'`（陆地）和 `'0'`（水）组成的二维网格。统计并返回岛屿的数量。岛屿由 `'1'` 连接形成（水平或垂直相邻）。

```
输入：grid = [
  ["1","1","0","0","0"],
  ["1","1","0","0","0"],
  ["0","0","1","0","0"],
  ["0","0","0","1","1"]
]
输出：3
```

```csharp
public int NumIslands(char[][] grid) {
    int count = 0, m = grid.Length, n = grid[0].Length;
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            if (grid[i][j] == '1') {
                count++;
                Dfs(i, j);
            }
    return count;
    void Dfs(int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != '1') return;
        grid[r][c] = '0';
        Dfs(r+1, c); Dfs(r-1, c); Dfs(r, c+1); Dfs(r, c-1);
    }
}
```

**解题思路：** 遍历每个格子，遇到 `1` 就 BFS/DFS 将其所有相连的 `1` 标记为 `0`（沉没），岛屿计数加一。沉没过程用 DFS 递归向四个方向扩展。**核心：连通分量计数 = 沉没次数**。

---

#### 994. 腐烂的橘子

**题设：** 给你一个网格，每个格子中有新鲜橘子、腐烂橘子或空格子。每分钟，腐烂橘子会把上下左右四个方向的新鲜橘子腐烂。返回直到没有新鲜橘子为止所需的分钟数；无法全部腐烂返回 -1。

```
输入：grid = [[2,1,1],[1,1,0],[0,1,1]]
输出：4
```

```csharp
public int OrangesRotting(int[][] grid) {
    int m = grid.Length, n = grid[0].Length, fresh = 0;
    var q = new Queue<(int, int)>();
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++) {
            if (grid[i][j] == 2) q.Enqueue((i, j));
            else if (grid[i][j] == 1) fresh++;
        }
    if (fresh == 0) return 0;
    int[][] dirs = { new[]{1,0}, new[]{-1,0}, new[]{0,1}, new[]{0,-1} };
    int days = 0;
    while (q.Count > 0) {
        int sz = q.Count;
        for (int k = 0; k < sz; k++) {
            var (r, c) = q.Dequeue();
            foreach (var d in dirs) {
                int nr = r + d[0], nc = c + d[1];
                if (nr >= 0 && nr < m && nc >= 0 && nc < n && grid[nr][nc] == 1) {
                    grid[nr][nc] = 2;
                    fresh--;
                    q.Enqueue((nr, nc));
                }
            }
        }
        if (q.Count > 0) days++;
    }
    return fresh == 0 ? days : -1;
}
```

**解题思路：** 多源 BFS。所有腐烂橘子 `(2)` 同时作为初始队列，按层展开（每层代表一分钟）。四个方向扩散到新鲜橘子 `(1)`，使其腐烂并入队。遍历结束后检查是否还有新鲜橘子：有则返回 -1，无则返回分钟数。**多源 BFS = 最短路径的层序扩展**。

---

#### 79. 单词搜索

**题设：** 给定一个 `m x n` 字符网格 `board` 和一个字符串 `word`，判断 `word` 是否存在于网格中。路径可以从水平或垂直方向的相邻单元格构成，且路径上的每个单元格中的字符都相同。

```csharp
public bool Exist(char[][] board, string word) {
    int m = board.Length, n = board[0].Length;
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            if (Dfs(i, j, 0)) return true;
    return false;
    bool Dfs(int r, int c, int idx) {
        if (idx == word.Length) return true;
        if (r < 0 || c < 0 || r >= m || c >= n || board[r][c] != word[idx]) return false;
        char tmp = board[r][c];
        board[r][c] = '#';
        bool res = Dfs(r+1, c, idx+1) || Dfs(r-1, c, idx+1)
                || Dfs(r, c+1, idx+1) || Dfs(r, c-1, idx+1);
        board[r][c] = tmp;
        return res;
    }
}
```

**解题思路：** DFS 枚举起点，在网格中搜索单词。用 `#` 标记已访问（避免重复），搜索完后恢复。**注意：需要恢复 board 的值（撤销选择），因为一个格子不能在一个路径中被使用两次**。

---

#### 130. 被围绕的区域

**题设：** 给你一个 `m x n` 的矩阵 `board`，包含 `'X'` 和 `'O'`。将被 `'X'` 完全围绕的 `'O'` 区域替换为 `'X'`。边界上的 `'O'` 不能被替换。

```csharp
public void Solve(char[][] board) {
    int m = board.Length, n = board[0].Length;
    for (int i = 0; i < m; i++) {
        Dfs(i, 0); Dfs(i, n - 1);
    }
    for (int j = 0; j < n; j++) {
        Dfs(0, j); Dfs(m - 1, j);
    }
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++) {
            if (board[i][j] == 'O') board[i][j] = 'X';
            else if (board[i][j] == '#') board[i][j] = 'O';
        }
    void Dfs(int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || board[r][c] != 'O') return;
        board[r][c] = '#';
        Dfs(r+1, c); Dfs(r-1, c); Dfs(r, c+1); Dfs(r, c-1);
    }
}
```

**解题思路：** 从边界上的 `'O'` 出发，DFS 把所有与边界连通的 `'O'` 标记为 `#`（表示不会被替换）。完成后，遍历整个矩阵：剩余的 `'O'` 就是被 `'X'` 包围的区域（改为 `'X'`），`#` 恢复为 `'O'`。**先从边界 BFS/DFS 染色，再统一处理**，是解决"被围绕"类问题的标准套路。

---

### 拓扑排序 / 课程表

#### 207. 课程表

**题设：** 你要选修 `numCourses` 门课程，课程编号 0 到 numCourses-1。给定数组 `prerequisites`，其中 `prerequisites[i] = [ai, bi]` 表示要选修课程 `ai` 必须先选修课程 `bi`。判断是否能完成所有课程。

```csharp
public bool CanFinish(int numCourses, int[][] prerequisites) {
    var inDeg = new int[numCourses];
    var adj = new List<int>[numCourses];
    for (int i = 0; i < numCourses; i++) adj[i] = new List<int>();
    foreach (var p in prerequisites) {
        adj[p[1]].Add(p[0]);
        inDeg[p[0]]++;
    }
    var q = new Queue<int>();
    for (int i = 0; i < numCourses; i++)
        if (inDeg[i] == 0) q.Enqueue(i);
    int visited = 0;
    while (q.Count > 0) {
        int u = q.Dequeue();
        visited++;
        foreach (int v in adj[u]) {
            if (--inDeg[v] == 0) q.Enqueue(v);
        }
    }
    return visited == numCourses;
}
```

**解题思路：** 检测有向图是否有环。计算所有节点的入度，初始入度为 0 的节点入队（BFS 起点）。出队时访问节点，将其邻接节点的入度减一，若入度变为 0 则入队。最终若访问了所有节点（`visited == numCourses`）则无环，否则有环。**BFS 拓扑排序 = Kahn 算法**。

---

#### 127. 单词接龙（困难）

**题设：** 给定两个单词 `beginWord` 和 `endWord` 以及单词列表 `wordList`，找出从 `beginWord` 到 `endWord` 的最短转换序列长度。一次只能改变一个字母，且每个中间单词必须在列表中。

```csharp
public int LadderLength(string beginWord, string endWord, IList<string> wordList) {
    var set = new HashSet<string>(wordList);
    if (!set.Contains(endWord)) return 0;
    var q = new Queue<string>();
    q.Enqueue(beginWord);
    int steps = 1;
    while (q.Count > 0) {
        int sz = q.Count;
        for (int s = 0; s < sz; s++) {
            string word = q.Dequeue();
            char[] chars = word.ToCharArray();
            for (int i = 0; i < chars.Length; i++) {
                char orig = chars[i];
                for (char c = 'a'; c <= 'z'; c++) {
                    chars[i] = c;
                    string next = new string(chars);
                    if (next == endWord) return steps + 1;
                    if (set.Contains(next)) { q.Enqueue(next); set.Remove(next); }
                }
                chars[i] = orig;
            }
        }
        steps++;
    }
    return 0;
}
```

**解题思路：** BFS 从 beginWord 出发，每次尝试改变一个字母生成所有可能的单词。若出现在 wordList 中则入队并移除（避免重复访问）。找到 endWord 时返回步数。

---

## 8. 回溯 (Backtracking)

#### 46. 全排列

**题设：** 给定一个不含重复数字的整数数组 `nums`，返回其所有可能的全排列。

```csharp
public IList<IList<int>> Permute(int[] nums) {
    var res = new List<IList<int>>();
    Backtrack(new List<int>(), new bool[nums.Length]);
    return res;
    void Backtrack(List<int> path, bool[] used) {
        if (path.Count == nums.Length) { res.Add(new List<int>(path)); return; }
        for (int i = 0; i < nums.Length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.Add(nums[i]);
            Backtrack(path, used);
            path.RemoveAt(path.Count - 1);
            used[i] = false;
        }
    }
}
```

**解题思路：** 对每个位置尝试所有未使用过的数。用 `used[]` 标记是否在当前路径中，递归到路径长度等于数组长度时加入结果。**核心：选→递归→撤销**。时间 O(n! * n)，空间 O(n) 递归栈。

---

#### 78. 子集

**题设：** 给你一个整数数组 `nums`，返回该数组的所有子集（幂集）。子集元素可以按任意顺序排列。

```csharp
public IList<IList<int>> Subsets(int[] nums) {
    var res = new List<IList<int>>();
    Backtrack(0, new List<int>());
    return res;
    void Backtrack(int start, List<int> path) {
        res.Add(new List<int>(path));
        for (int i = start; i < nums.Length; i++) {
            path.Add(nums[i]);
            Backtrack(i + 1, path);
            path.RemoveAt(path.Count - 1);
        }
    }
}
```

**解题思路：** 从前往后选或不选每个元素，构成所有可能的子集。每次递归都在结果中加入当前路径（**每个节点都是结果**，对应一个子集）。选当前数则继续递归，回溯后不选。**与排列不同：不需要 used 数组，因为子集关心元素是否被选，不关心顺序**。

---

#### 17. 电话号码的字母组合

**题设：** 给定数字字符串 `digits`，返回它可能代表的所有字母组合。数字到字母的映射与电话键盘相同。

```
2 -> abc, 3 -> def, 4 -> ghi, 5 -> jkl, 6 -> mno,
7 -> pqrs, 8 -> tuv, 9 -> wxyz
输入："23"  → ["ad","ae","af","bd","be","bf","cd","ce","cf"]
```

```csharp
public IList<string> LetterCombinations(string digits) {
    if (digits.Length == 0) return new List<string>();
    string[] map = { "", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz" };
    var res = new List<string>();
    Backtrack(0, "");
    return res;
    void Backtrack(int idx, string path) {
        if (idx == digits.Length) { res.Add(path); return; }
        foreach (char c in map[digits[idx] - '0'])
            Backtrack(idx + 1, path + c);
    }
}
```

**解题思路：** 建立数字到字母的映射，递归深度为 digits 长度。每一层遍历当前数字对应的所有字母，加入路径后递归下一层。**本质：数字串的笛卡尔积**，可理解为多叉树的遍历。

---

#### 39. 组合总和

**题设：** 给你一个无重复元素的整数数组 `candidates` 和一个目标整数 `target`，找出所有和等于 `target` 的组合。candidates 中的数字可以无限制重复选取。组合内的数字必须非降序排列。

```csharp
public IList<IList<int>> CombinationSum(int[] candidates, int target) {
    var res = new List<IList<int>>();
    Backtrack(0, target, new List<int>());
    return res;
    void Backtrack(int start, int remain, List<int> path) {
        if (remain < 0) return;
        if (remain == 0) { res.Add(new List<int>(path)); return; }
        for (int i = start; i < candidates.Length; i++) {
            path.Add(candidates[i]);
            Backtrack(i, remain - candidates[i], path);
            path.RemoveAt(path.Count - 1);
        }
    }
}
```

**解题思路：** 先排序保证组合内数字非降序。递归时 `start=i`（允许重复选当前数），目标值减去当前数。当 `remain < 0` 剪枝返回，`remain == 0` 时找到一个有效组合。**排序 + start 索引 + remain 递减**，这是组合总和类回溯的标准模板。

---

#### 131. 分割回文串

**题设：** 给你字符串 `s`，将其分割成若干非空子串，每个子串都是回文串。返回所有可能的分割方案。

```csharp
public IList<IList<string>> Partition(string s) {
    var res = new List<IList<string>>();
    Backtrack(0, new List<string>());
    return res;
    void Backtrack(int start, List<string> path) {
        if (start == s.Length) { res.Add(new List<string>(path)); return; }
        for (int i = start; i < s.Length; i++) {
            if (IsPal(s, start, i)) {
                path.Add(s.Substring(start, i - start + 1));
                Backtrack(i + 1, path);
                path.RemoveAt(path.Count - 1);
            }
        }
    }
    bool IsPal(string str, int l, int r) {
        while (l < r) if (str[l++] != str[r--]) return false;
        return true;
    }
}
```

**解题思路：** 枚举每一个可能的分割点，判断截取的子串是否为回文。是回文则加入路径继续递归。**先判断再递归**（不同于组合总和的先递归后判断）。可用动态规划预处理回文以加速。

---

## 9. 堆 / 优先队列

#### 215. 数组第 K 大

**题设：** 给你整数数组 `nums` 和整数 `k`，返回数组中第 `k` 大的元素（第 1 大是最大值）。

```csharp
public int FindKthLargest(int[] nums, int k) {
    var pq = new PriorityQueue<int, int>();
    foreach (int n in nums) {
        pq.Enqueue(n, -n);
        if (pq.Count > k) pq.Dequeue();
    }
    return pq.Dequeue();
}
```

**解题思路：** 维护一个大小为 k 的小顶堆。遍历所有元素，入堆并保持堆大小为 k（超过 k 时弹出堆顶）。最终堆顶即为第 k 大的元素。时间 O(n log k)，优于排序的 O(n log n)。也可用快速选择 O(n) 解决。

---

#### 347. 前 K 个高频元素

**题设：** 给你整数数组 `nums` 和整数 `k`，返回出现频率最高的 `k` 个元素。答案按频率从高到低排序。

```csharp
public int[] TopKFrequent(int[] nums, int k) {
    var freq = new Dictionary<int, int>();
    foreach (int n in nums) freq[n] = freq.GetValueOrDefault(n) + 1;
    var pq = new PriorityQueue<int, int>();
    foreach (var kv in freq) pq.Enqueue(kv.Key, kv.Value);
    var res = new List<int>();
    for (int i = 0; i < k; i++) res.Add(pq.Dequeue());
    return res.ToArray();
}
```

**解题思路：** 先用字典统计频率，然后用最大堆（或最小堆取 top-k）排序。**PriorityQueue 默认是最小堆，传入 `-freq` 可实现最大堆**。也可用桶排序：频率范围是 [1, n]，按频率分桶直接收集。

---

#### 23. 合并 K 个有序链表

**题设：** 合并 `k` 个升序链表为一个升序链表，返回合并后的链表头。

```csharp
public ListNode MergeKLists(ListNode[] lists) {
    var pq = new PriorityQueue<ListNode, int>();
    foreach (var l in lists) if (l != null) pq.Enqueue(l, l.val);
    ListNode dummy = new ListNode(0), cur = dummy;
    while (pq.Count > 0) {
        var node = pq.Dequeue();
        cur.next = node;
        if (node.next != null) pq.Enqueue(node.next, node.next.val);
        cur = cur.next;
    }
    return dummy.next;
}
```

**解题思路：** 用最小堆依次取出所有链表当前最小的头节点。入堆所有链表的头（跳过 null），弹出堆顶接入结果链表，若弹出的节点还有 next 则入堆。**时间 O(N log K)**，N 为总节点数，K 为链表数。

---

#### 295. 数据流中位数（困难）

**题设：** 设计一个数据结构，支持：① 添加整数；② 返回到目前为止所有整数的中位数。要求两个操作的时间复杂度均为 O(log N)。

```csharp
public class MedianFinder {
    PriorityQueue<int, int> lo = new();
    PriorityQueue<int, int> hi = new();
    public void AddNum(int num) {
        lo.Enqueue(num, -num);
        hi.Enqueue(lo.Dequeue(), lo.Count >= hi.Count ? 0 : 1);
        if (lo.Count < hi.Count) lo.Enqueue(hi.Dequeue(), -hi.Peek());
    }
    public double FindMedian() {
        return lo.Count > hi.Count ? lo.Peek() : (lo.Peek() + hi.Peek()) / 2.0;
    }
}
```

**解题思路：** 维护两个堆——`lo` 是最大堆（存较小的一半数），`hi` 是最小堆（存较大的一半数）。始终保持 `|lo.Count - hi.Count| <= 1` 且 `lo.Count >= hi.Count`。中位数即 `lo` 的堆顶（奇数时）或两个堆顶的平均（偶数时）。**添加时：加入 lo → lo 弹一个到 hi → 若 hi 更多则弹回 lo，保持平衡**。

---

## 10. 二分查找

#### 704. 二分查找（标准模板）

**题设：** 给定一个 `n` 个元素升序数组 `nums` 和目标值 `target`，返回 `target` 在数组中的索引，若不存在返回 -1。

```csharp
public int Search(int[] nums, int target) {
    int l = 0, r = nums.Length - 1;
    while (l <= r) {
        int mid = l + (r - l) / 2;
        if (nums[mid] == target) return mid;
        else if (nums[mid] < target) l = mid + 1;
        else r = mid - 1;
    }
    return -1;
}
```

**解题思路：** 左闭右闭区间 `[l, r]`。每次取中点比较：等于目标直接返回；小于目标 `l = mid + 1`；大于目标 `r = mid - 1`。循环条件 `l <= r`。**模板：while(l <= r) → 中点 → 判断 → 缩边界**。

---

#### 33. 搜索旋转排序数组

**题设：** 给你一个升序数组（可能有重复元素）在某处旋转后的数组，以及目标值 `target`，返回 `target` 在数组中的索引，或 -1。

```
输入：nums = [4,5,6,7,0,1,2], target = 0  → 输出：4
```

```csharp
public int Search2(int[] nums, int target) {
    int l = 0, r = nums.Length - 1;
    while (l <= r) {
        int mid = l + (r - l) / 2;
        if (nums[mid] == target) return mid;
        if (nums[l] <= nums[mid]) {
            if (nums[l] <= target && target < nums[mid]) r = mid - 1;
            else l = mid + 1;
        } else {
            if (nums[mid] < target && target <= nums[r]) l = mid + 1;
            else r = mid - 1;
        }
    }
    return -1;
}
```

**解题思路：** 二分查找的变形。旋转数组有一半是有序的。判断哪一半有序：若 `nums[l] <= nums[mid]`，则左半边有序；否则右半边有序。然后判断 target 是否落在有序半边内，决定去哪半边搜索。**核心：每次二分必有一半是有序数组**。

---

#### 162. 寻找峰值

**题设：** 给你一个整数数组 `nums`（相邻数不相等），返回一个峰值元素的索引。数组两端可视为负无穷。峰值：比相邻元素都大的元素。假设 `nums[-1] = nums[n] = -∞`。

```csharp
public int FindPeakElement(int[] nums) {
    int l = 0, r = nums.Length - 1;
    while (l < r) {
        int mid = l + (r - l) / 2;
        if (nums[mid] > nums[mid + 1]) r = mid;
        else l = mid + 1;
    }
    return l;
}
```

**解题思路：** 二分查找找峰值。由于边界处可视为负无穷，峰值必然存在且不唯一。比较 `nums[mid]` 和 `nums[mid+1]`：若上升（`nums[mid] < nums[mid+1]`），则峰值在右边；若下降则在左边。由于 `mid+1` 存在保证 `l < r` 条件。

---

#### 69. x 的平方根

**题设：** 给你一个非负整数 `x`，返回 `x` 的算术平方根的整数部分。

```csharp
public int MySqrt(int x) {
    long l = 0, r = x;
    while (l <= r) {
        long mid = l + (r - l) / 2;
        if (mid * mid <= x) { l = mid + 1; }
        else r = mid - 1;
    }
    return (int)r;
}
```

**解题思路：** 二分查找找 `mid² <= x` 的最大 `mid`。注意用 `long` 防止溢出，返回 `r`（因为 r 是最后一个满足条件的值）。

---

#### 74. 搜索二维矩阵

**题设：** 给你一个 `m x n` 的矩阵，每行整数严格递增，且每行第一个整数比上一行最后一个整数大。判断目标值是否在矩阵中。

```csharp
public bool SearchMatrix(int[][] matrix, int target) {
    int m = matrix.Length, n = matrix[0].Length;
    int l = 0, r = m * n - 1;
    while (l <= r) {
        int mid = l + (r - l) / 2;
        int val = matrix[mid / n][mid % n];
        if (val == target) return true;
        else if (val < target) l = mid + 1;
        else r = mid - 1;
    }
    return false;
}
```

**解题思路：** 将二维矩阵当成一维数组二分。通过 `matrix[mid/n][mid%n]` 映射到二维坐标。时间 O(log(mn))。**也可以先二分行再二分列，但不如直接映射简洁**。

---

#### 278. 第一个错误的版本

**题设：** 你是一个产品经理，当前处于第 1 天。产品每个版本都会导致后续版本出错（即版本链是 000...000111...111 的形式）。给定 `n`，返回第一个错误版本的下标。

```csharp
public int FirstBadVersion(int n) {
    int l = 1, r = n;
    while (l < r) {
        int mid = l + (r - l) / 2;
        if (IsBadVersion(mid)) r = mid;
        else l = mid + 1;
    }
    return l;
}
```

**解题思路：** 标准二分查找的变形。找第一个满足 `IsBadVersion(mid) == true` 的位置。**注意循环条件是 `l < r`（不等于），返回 `l`**。

---

## 11. 并查集 (Union-Find)

#### 547. 省份数量

**题设：** 给你 `n` 个城市和 `n x n` 的连接矩阵 `isConnected`，其中 `isConnected[i][j] = 1` 表示第 i 个城市和第 j 个城市直接相连。返回省份的数量（连通分量的数量）。

```csharp
public class UnionFind {
    int[] parent, rank;
    public int count;
    public UnionFind(int n) {
        parent = new int[n]; rank = new int[n]; count = n;
        for (int i = 0; i < n; i++) parent[i] = i;
    }
    public int Find(int x) => parent[x] == x ? x : parent[x] = Find(parent[x]);
    public void Union(int x, int y) {
        int rx = Find(x), ry = Find(y);
        if (rx == ry) return;
        if (rank[rx] < rank[ry]) { parent[rx] = ry; }
        else if (rank[rx] > rank[ry]) { parent[ry] = rx; }
        else { parent[ry] = rx; rank[rx]++; }
        count--;
    }
}
```

**解题思路：** 初始化每个节点为独立集合，count = n。遍历所有边 `(isConnected[i][j])`，若相连则 union。若 i == j 自动跳过。遍历结束后 count 即为连通分量数量（省份数量）。**路径压缩 + 按秩合并**保证近乎 O(1) 的时间复杂度。

---

#### 684. 冗余连接

**题设：** 给定一个包含 `n` 个节点的树（n 个节点，n-1 条边），再加入一条边后形成环。找到那条导致环的边，将其移除后使图重新成为一棵树。

```csharp
public int[] FindRedundantConnection(int[][] edges) {
    var uf = new UnionFind(edges.Length + 1);
    foreach (var e in edges) {
        if (uf.Find(e[0]) == uf.Find(e[1])) return e;
        uf.Union(e[0], e[1]);
    }
    return new int[0];
}
```

**解题思路：** 并查集的经典应用。遍历所有边，若两端已连通则这条边就是导致环的那条边（因为树中不应有环）。否则 union。最终返回导致环的那条边。

---

## 12. 单调栈

#### 496. 下一个更大元素 I

**题设：** 给你两个没有重复元素的数组 `nums1` 和 `nums2`。`nums1` 是 `nums2` 的子集。在 `nums2` 中找出每个元素右侧第一个比它大的值，构建答案数组。

```csharp
public int[] NextGreaterElement(int[] nums1, int[] nums2) {
    var dict = new Dictionary<int, int>();
    var stack = new Stack<int>();
    for (int i = nums2.Length - 1; i >= 0; i--) {
        while (stack.Count > 0 && stack.Peek() <= nums2[i]) stack.Pop();
        dict[nums2[i]] = stack.Count == 0 ? -1 : stack.Peek();
        stack.Push(nums2[i]);
    }
    return nums1.Select(x => dict[x]).ToArray();
}
```

**解题思路：** 从右往左遍历 nums2，维护一个递减栈（栈中元素从栈底到栈顶递减）。对于每个数，弹出所有小于等于它的栈顶（因为它们不会有下一个更大元素），栈顶即为答案。然后将当前数入栈。**倒序遍历 + 单调递减栈 = 每个元素第一次看到的都是"右边第一个更大"**。

---

#### 84. 柱状图中最大的矩形

**题设：** 给定 `n` 个非负整数表示柱状图的高度，每个柱子的宽度为 1。找出其中能勾勒出的最大矩形面积。

```
输入：heights = [2,1,5,6,2,3]  → 输出：10（5 和 6 高度，宽度 2）
```

```csharp
public int LargestRectangleArea(int[] heights) {
    var stack = new Stack<int>();
    int ans = 0;
    for (int i = 0; i <= heights.Length; i++) {
        int cur = i == heights.Length ? 0 : heights[i];
        while (stack.Count > 0 && heights[stack.Peek()] > cur) {
            int h = heights[stack.Pop()];
            int w = stack.Count == 0 ? i : i - stack.Peek() - 1;
            ans = Math.Max(ans, h * w);
        }
        stack.Push(i);
    }
    return ans;
}
```

**解题思路：** 单调递增栈。遍历每个柱子和一个虚拟的"高度为 0"的柱子结尾。当遇到比栈顶矮的柱子时，弹出栈顶作为待计算矩形的高度 h，其左边界为栈中下一个元素的位置，右边界为当前遍历位置 i。宽 = `i - stack.Peek() - 1`。**核心：以每个柱为最高点的最大矩形面积**。

---

#### 739. 每日温度

**题设：** 给定一个整数数组 `temperatures` 表示每天的温度，返回一个数组 `answer`：若第 i 天的温度为 `temperatures[i]`，`answer[i]` = 需要等多少天才能遇到更高温度；若不存在则填 0。

```csharp
public int[] DailyTemperatures(int[] temperatures) {
    int n = temperatures.Length;
    int[] answer = new int[n];
    var stack = new Stack<int>();
    for (int i = 0; i < n; i++) {
        while (stack.Count > 0 && temperatures[i] > temperatures[stack.Peek()]) {
            int prev = stack.Pop();
            answer[prev] = i - prev;
        }
        stack.Push(i);
    }
    return answer;
}
```

**解题思路：** 单调递增栈（存索引）。遍历每天温度，若高于栈顶对应的温度，则栈顶元素找到更高温度，弹出并填入天数差。否则入栈。**核心：栈中索引对应的温度单调递增**。

---

## 高频面试必背清单

| 优先级 | 题型 | 推荐必刷题 |
|--------|------|-----------|
| ★★★ | 双指针 + 滑动窗口 | 3, 11, 15, 42, 167, 977, 88 |
| ★★★ | 链表操作 | 141, 160, 206, 21, 92, 234, 25, 86 |
| ★★★ | DFS/BST | 98, 104, 110, 543, 226, 112, 437, 101, 102 |
| ★★★ | 动态规划路径/背包 | 62, 64, 198, 322, 416, 474, 221, 5 |
| ★★★ | 二分查找 | 704, 33, 162, 69, 74, 278 |
| ★★ | 回溯 | 46, 78, 17, 39, 131, 79 |
| ★★ | 图/BFS | 200, 994, 207, 127, 130 |
| ★★ | 堆/优先队列 | 215, 347, 23, 295 |
| ★ | 贪心 | 55, 45, 435, 452, 56, 763 |
| ★ | 单调栈 | 84, 496, 739 |
| ★ | 并查集 | 547, 684 |

---

## C# 面试代码技巧

```csharp
// 1. 空合并运算符
cur.next = l1 ?? l2;

// 2. Tuple 解构
var (r, c) = (1, 2);

// 3. Span 高效切片（避免字符串分配）
Span<int> span = numbers;
// span.Slice(1, 3)

// 4. 用 List<int> 当动态数组时，记得 .Add/.RemoveAt
// 5. 二维数组初始化：int[][] dp = new int[m+1][];

// 6. 字典快速判断
if (dict.TryGetValue(key, out int val))

// 7. 优先队列（.NET 6+，最小堆默认）
var pq = new PriorityQueue<TElement, TPriority>();
pq.Enqueue(item, priority);
pq.Dequeue();

// 8. Array.Sort 降序
Array.Sort(arr, (a, b) => b.CompareTo(a));

// 9. 字符串重复拼接用 StringBuilder
var sb = new StringBuilder();
sb.Append(c);

// 10. 数组比较（用于滑动窗口计数）
need.SequenceEqual(cur)  // 需要 using System.Linq;

// 11. char[] 批量修改
char[] chars = s.ToCharArray();
// 修改后再 string s2 = new string(chars);

// 12. 二维数组行列长度
int m = grid.Length, n = grid[0].Length;
```

---

## 各题型核心模板速查

**链表快慢指针** — `slow=slow.next; fast=fast.next.next`

**反转链表** — `cur.next=prev; prev=cur; cur=next`

**滑动窗口** — `右扩→while收缩→更新ans`

**二叉树 DFS** — `dfs(node) { if null return; 处理; dfs(left); dfs(right); }`

**二叉树 BFS** — `while q.Count>0 { int cnt=q.Count; for(cnt){ Dequeue+Enqueue children} }`

**回溯** — `选→递归→撤销（used/RemoveAt）`

**0/1 背包** — `for j=target→w { dp[j]=dp[j]||dp[j-w] }`（倒序）

**完全背包** — `for j=w→target { dp[j]=min(dp[j],dp[j-w]+1) }`（正序）

**单调栈** — `while stack.Count>0 && 当前<=栈顶 { pop } 处理; push`

**K路归并** — `PriorityQueue，每次取最小，弹出后入next`

**图/岛屿沉没** — `grid[r][c]='0'; dfs上下左右; count++`

**拓扑排序** — `入度0入队→出队减邻接入度→新0入队→判断visited==numCourses`

祝你面试顺利！
