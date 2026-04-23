import json


def get_examples():
    examples = {}
    examples["gsm8k"] = [
        (
            "There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?",
            "There are 15 trees originally. Then there were 21 trees after some more were planted. So there must have been 21 - 15 = 6. The answer is 6.",
        ),
        (
            "If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?",
            "There are originally 3 cars. 2 more cars arrive. 3 + 2 = 5. The answer is 5.",
        ),
        (
            "Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?",
            "Originally, Leah had 32 chocolates. Her sister had 42. So in total they had 32 + 42 = 74. After eating 35, they had 74 - 35 = 39. The answer is 39.",
        ),
        (
            "Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?",
            "Jason started with 20 lollipops. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = 8. The answer is 8.",
        ),
        (
            "Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?",
            "Shawn started with 5 toys. If he got 2 toys each from his mom and dad, then that is 4 more toys. 5 + 4 = 9. The answer is 9.",
        ),
        (
            "There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?",
            "There were originally 9 computers. For each of 4 days, 5 more computers were added. So 5 * 4 = 20 computers were added. 9 + 20 is 29. The answer is 29.",
        ),
        (
            "Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?",
            "Michael started with 58 golf balls. After losing 23 on tuesday, he had 58 - 23 = 35. After losing 2 more, he had 35 - 2 = 33 golf balls. The answer is 33.",
        ),
        (
            "Olivia has $23. She bought five bagels for $3 each. How much money does she have left?",
            "Olivia had 23 dollars. 5 bagels for 3 dollars each will be 5 x 3 = 15 dollars. So she has 23 - 15 dollars left. 23 - 15 is 8. The answer is 8.",
        ),
    ]
    examples["gsm8k-tora"] = [
        (
            "Olivia has $23. She bought five bagels for $3 each. How much money does she have left?",
            "```python\ndef money_left():\n    money_initial = 23\n    bagels = 5\n    bagel_cost = 3\n    money_spent = bagels * bagel_cost\n    remaining_money = money_initial - money_spent\n    return remaining_money\n \nremaining_money = money_left()\nprint(remaining_money)\n```\n```output\n8\n```\nOlivia has $\\boxed{8}$ dollars left.",
        ),
        (
            "Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?",
            "```python\ndef remaining_golf_balls():\n    golf_balls_initial = 58\n    golf_balls_lost_tuesday = 23\n    golf_balls_lost_wednesday = 2\n    golf_balls_left = golf_balls_initial - golf_balls_lost_tuesday - golf_balls_lost_wednesday\n    remaining_golf_balls = golf_balls_left\n    return remaining_golf_balls\n\nanswer = remaining_golf_balls() \nprint(answer)\n```\n```output\n33\n```\nMichael had $\\boxed{33}$ golf balls at the end of Wednesday.",
        ),
        (
            "There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?",
            "```python\ndef total_computers():\n    computers_initial = 9\n    computers_per_day = 5\n    num_days = 4  # 4 days between monday and thursday\n    computers_added = computers_per_day * num_days\n    computers_total = computers_initial + computers_added\n    return computers_total\n\ntotal_computers = total_computers()\nprint(total_computers)\n```\n```output\n29\n```\nThere're $\\boxed{29}$ computers in the server room.",
        ),
    ]

    examples["math"] = [
        (
            "Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.",
            "Let's think step by step\nKevin hops $1/3$ of the remaining distance with every hop.\nHis first hop takes $1/3$ closer.\nFor his second hop, he has $2/3$ left to travel, so he hops forward $(2/3)(1/3)$.\nFor his third hop, he has $(2/3)^2$ left to travel, so he hops forward $(2/3)^2(1/3)$.\nIn general, Kevin hops forward $(2/3)^{k-1}(1/3)$ on his $k$th hop.\nWe want to find how far he has hopped after five hops.\nThis is a finite geometric series with first term $1/3$, common ratio $2/3$, and five terms.\nThus, Kevin has hopped $\\frac{\\frac{1}{3}\\left(1-\\left(\\frac{2}{3}\\right)^5\\right)}{1-\\frac{2}{3}} = \\boxed{\\frac{211}{243}}$.\nThe answer is \\frac{211}{243}}",
        ),
        (
            "What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?",
            "Let's think step by step\nWe rewrite the equation as $x^2 + 14x + y^2 - 4y = 10$ and then complete the square,\nresulting in  $(x+7)^2-49 + (y-2)^2-4=10$,\nor $(x+7)^2+(y-2)^2=63$.\nThis is the equation of a circle with center $(-7, 2)$ and radius $\\sqrt{63},$\nso the area of this region is $\\pi r^2 = \\boxed{63\\pi}$.\nThe answer is 63\\pi",
        ),
        (
            "If $x^2+y^2=1$, what is the largest possible value of $|x|+|y|$?",
            "Let's think step by step\nIf $(x,y)$ lies on the circle,\nso does $(x,-y),$ $(-x,-y),$ and $(-x,-y),$ (which all give the same value of $|x| + |y|$),\nso we can assume that $x \\ge 0$ and $y \\ge 0.$\nThen $|x| + |y| = x + y.$  Squaring, we get\n\\[(x + y)^2 = x^2 + 2xy + y^2 = 1 + 2xy.\\]\nNote that $(x - y)^2 \\ge 0.$\nExpanding, we get $x^2 - 2xy + y^2 \\ge 0,$ so $2xy \\le x^2 + y^2 = 1.$\nHence,\\[1 + 2xy \\le 2,\\]which means $x + y \\le \\sqrt{2}.$\nEquality occurs when $x = y = \\frac{1}{\\sqrt{2}},$\nso the maximum value of $|x| + |y|$ is $\\boxed{\\sqrt{2}}.$\nThe answer is \\sqrt{2}",
        ),
        (
            "If $f(x)=\\frac{ax+b}{cx+d}, abcd\\not=0$ and $f(f(x))=x$ for all $x$ in the domain of $f$, what is the value of $a+d$?",
            "Let's think step by step\nThe condition $f(f(x))$ means that $f$ is the inverse of itself,\nso its graph is symmetrical about the line $y = x$.\nWith a rational function of this form, we will have two asymptotes:\na vertical one at $x=-d/c$ if $cx+d$ does not divide $ax+b$,\nand a horizontal one at $y=a/c$,\nif we take the limit of $f(x)$ as $x$ goes to $\\pm\\infty$.\nIn order for $f$ to be its own inverse, the intersection of the asymptotes must lie on the line $y=x$\nso that it and its asymptotes reflect onto themselves.\nThis means that $-d/c=a/c$,\nand therefore $-d=a$ and $a+d=\\boxed{0}$.\nThe answer is 0",
        ),
        (
            "Expand $(2z^2 + 5z - 6)(3z^3 - 2z + 1)$.",
            "Let's think step by step\n$$\\begin{array}{crrrrrrr}\n& & & 3z^3 & & -2z & + 1 & \\\\\n\\times & & & & 2z^2 & +5z & -6 \\\\\n\\cline{1-7}\\rule{0pt}{0.17in}\n& & & -18z^3 & & +12z & -6 & \\\\\n& & +15z^4 & & -10z^2 & +5z & & \\\\\n+ & 6z^5 & & -4z^3 & +2z^2 & & & \\\\\n\\cline{1-7}\\rule{0pt}{0.17in}\n& 6z^5 & +15z^4 & -22z^3 & - 8z^2 &+17z & -6 &\n\\end{array}$$\nThe answer is 6z^5+15z^4-22z^3-8z^2+17z-6",
        ),
    ]
    examples["math-tora"] = [
        (
            "Convert the point $(0, -3 \\sqrt{3}, 3)$ in rectangular coordinates to spherical coordinates.  Enter your answer in the form $(\\rho,\\theta,\\phi),$ where $\\rho > 0,$ $0 \\le \\theta < 2 \\pi,$ and $0 \\le \\phi \\le \\pi.$",
            "To convert the point $(x, y, z)$ in rectangular coordinates to spherical coordinates $(\\rho, \\theta, \\phi)$, we use the following formulas:\n1. $\\rho = \\sqrt{x^2 + y^2 + z^2}$\n2. $\\theta = \\arctan{\\frac{y}{x}}$\n3. $\\phi = \\arccos{\\frac{z}{\\rho}}$\n\nLet's write a function:\n\n```python\nfrom sympy import sqrt, atan2, acos, pi\n\ndef rectangular_to_spherical():\n    x, y, z = 0, -3*sqrt(3), 3\n    rho = sqrt(x**2 + y**2 + z**2)\n    theta = atan2(y, x)\n    phi = acos(z/rho)\n    return rho, theta, phi\n\nspherical_coordinates = rectangular_to_spherical()\nprint(spherical_coordinates)\n```\n```output\n(6, -pi/2, pi/3)\n```\n\nThe required form of the answer is $(\\rho, \\theta, \\phi)$, where $\\rho > 0$, $0 \\le \\theta < 2\\pi$, and $0 \\le \\phi \\le \\pi$. Since our initial output has $\\theta = -\\pi/2$, which doesn't meet the condition for $\\theta$, we add $2\\pi$ to adjust its value.\n\nHence, the spherical coordinates for the point $(0, -3\\sqrt{3}, 3)$ are $\\boxed{(6, \\frac{3\\pi}{2}, \\frac{\\pi}{3})}$.",
        ),
        (
            "Compute $1011_2 + 101_2 - 1100_2 + 1101_2$.  Express your answer in base 2.",
            'Let\'s write a single python function for binary computation:\n\n```python\ndef binary_sum_diff():\n    # Convert binary to decimal\n    num1 = int("1011", 2)\n    num2 = int("101", 2)\n    num3 = int("1100", 2)\n    num4 = int("1101", 2)\n\n    # Perform the operations\n    result = num1 + num2 - num3 + num4\n\n    # Convert the result back to binary\n    result_binary = format(result, "b")\n\n    return result_binary\n\nresult = binary_sum_diff()\nprint(result)\n```\n```output\n10001\n```\nThe answer expressed in base 2 is $\\boxed{10001_2}$.',
        ),
        (
            "Find the matrix that corresponds to projecting onto the vector $\\begin{pmatrix} 2 \\\\ -3 \\end{pmatrix}.$",
            "```python\nfrom sympy import Matrix, simplify\n\ndef projection_matrix():\n    v = Matrix([2, -3])\n\n    # Calculate the projection matrix\n    P = (v * v.T) / (v.T * v)[0]\n\n    # Simplify the elements\n    P = P.applyfunc(simplify)\n\n    return P\n\nresult = projection_matrix()\nprint(result)\n```\n```output\nMatrix([[4/13, -6/13], [-6/13, 9/13]])\n```\n\nThe matrix is $\\boxed{\\begin{pmatrix} \\frac{4}{13} & -\\frac{6}{13} \\ -\\frac{6}{13} & \\frac{9}{13} \\end{pmatrix}}.$",
        ),
        (
            "Solve the inequality\n\\[\\frac{x^2 - 25}{x + 5} < 0.\\]",
            "Let's use `sympy` to solve the inequality:\n\n```python\nfrom sympy import symbols, simplify\nfrom sympy.solvers.inequalities import solve_univariate_inequality\nfrom sympy.core.relational import StrictLessThan\n\ndef solve_inequality():\n    x = symbols('x')\n    expression = (x**2 - 25) / (x + 5)\n    inequality = StrictLessThan(expression, 0)\n    solution = solve_univariate_inequality(inequality, x, relational=False)\n    simplified_solution = simplify(solution)\n    \n    return simplified_solution\n\nresult = solve_inequality()\nprint(result)\n```\n```output\nUnion(Interval.open(-oo, -5), Interval.Lopen(-5, 5))\n```\nThe answer is $\\boxed{(-\\infty,-5)\\cup(-5,5)}$",
        ),
        (
            'In the figure, triangles $ABC$ and $BCD$ are equilateral triangles. What is the value of $AD \\div BC$ when expressed in simplest radical form?\n\n[asy]\ndraw((0,0)--(5,8.7)--(10,0)--cycle);\ndraw((10,0)--(15,8.7)--(5,8.7));\nlabel("$A$",(0,0),SW);\nlabel("$B$",(5,8.7),N);\nlabel("$C$",(10,0),SE);\nlabel("$D$",(15,8.7),NE);\n[/asy]',
            "```python\nfrom sympy import Rational, sqrt, simplify\n\ndef ad_divided_by_bc():\n\n    x = Rational(1, 1)  # Side length of equilateral triangles\n\n    ad_squared = 2 * x**2 * (1 + Rational(1, 2))  # Using the law of cosines with cos(2*pi/3) = -1/2\n    ad = sqrt(ad_squared)\n\n    bc = x # BC is the side length of the equilateral triangles\n\n    simplified_ratio = simplify(ad / bc)\n\n    return simplified_ratio\n\nresult = ad_divided_by_bc()\nprint(result)\n```\n```output\nsqrt(3)\n```\nThe value of $AD \\div BC$ is $\\boxed{\\sqrt{3}}$.",
        ),
    ]

    return examples