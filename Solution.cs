using System;

namespace Solution
{
    class Program
    {
        static void Main(string[] args)
        {
            string a = "1010";
            string b = "1011";

            int i = a.Length - 1;  // 指向 a 的最右侧
            int j = b.Length - 1;  // 指向 b 的最右侧
            int carry = 0;
            char[] res = new char[Math.Max(a.Length, b.Length) + 1];
            int pos = res.Length - 1;  // 指向 res 的最右侧

            while (i >= 0 || j >= 0 || carry > 0)
            {
                int bitA = i >= 0 ? a[i] - '0' : 0;
                int bitB = j >= 0 ? b[j] - '0' : 0;
                int sum = bitA + bitB + carry;

                res[pos] = (sum % 2).ToString()[0];
                carry = sum / 2;

                i--;
                j--;
                pos--;
            }

            // 去掉前导零
            string result = new string(res).TrimStart('0');
            if (result == "") result = "0";

            Console.WriteLine(result);
        }
    }
}
