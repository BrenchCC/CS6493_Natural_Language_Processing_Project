"""Shared prompt exemplars for few-shot CoT and TIR methods."""

from typing import Dict
from typing import List
from typing import Tuple


Example = Tuple[str, str]
ExampleMap = Dict[str, List[Example]]


def get_examples() -> ExampleMap:
    """Return curated examples grouped by dataset family."""
    examples: ExampleMap = {}
    examples["gsm8k"] = [
        (
            "There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?",
            "We start with 15 trees and end with 21 trees. The number planted is $21 - 15 = 6$.\nFinal Answer: \\boxed{6}",
        ),
        (
            "Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?",
            "Together they had $32 + 42 = 74$ chocolates. After eating 35, they had $74 - 35 = 39$ left.\nFinal Answer: \\boxed{39}",
        ),
        (
            "There were nine computers in the server room. Five more computers were installed each day, from Monday to Thursday. How many computers are now in the server room?",
            "From Monday to Thursday is 4 days, so the new computers added total $5 \times 4 = 20$. Starting from 9 computers gives $9 + 20 = 29$.\nFinal Answer: \\boxed{29}",
        ),
        (
            "Michael had 58 golf balls. On Tuesday, he lost 23 golf balls. On Wednesday, he lost 2 more. How many golf balls did he have at the end of Wednesday?",
            "After Tuesday, Michael had $58 - 23 = 35$ golf balls. After Wednesday, he had $35 - 2 = 33$ golf balls.\nFinal Answer: \\boxed{33}",
        ),
        (
            "Olivia has $23. She bought five bagels for $3 each. How much money does she have left?",
            "The bagels cost $5 \times 3 = 15$ dollars. Olivia has $23 - 15 = 8$ dollars left.\nFinal Answer: \\boxed{8}",
        ),
    ]
    examples["gsm8k-tora"] = [
        (
            "Olivia has $23. She bought five bagels for $3 each. How much money does she have left?",
            "```python\nprint(23 - 5 * 3)\n```\n```output\n8\n```\nFinal Answer: \\boxed{8}",
        ),
        (
            "Michael had 58 golf balls. On Tuesday, he lost 23 golf balls. On Wednesday, he lost 2 more. How many golf balls did he have at the end of Wednesday?",
            "```python\nprint(58 - 23 - 2)\n```\n```output\n33\n```\nFinal Answer: \\boxed{33}",
        ),
        (
            "There were nine computers in the server room. Five more computers were installed each day, from Monday to Thursday. How many computers are now in the server room?",
            "```python\nprint(9 + 5 * 4)\n```\n```output\n29\n```\nFinal Answer: \\boxed{29}",
        ),
    ]
    examples["math"] = [
        (
            "Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.",
            "Each hop covers $\\frac{1}{3}$ of the remaining distance, so the total distance traveled after five hops is the geometric sum\n$$\\frac{1}{3} + \\frac{2}{3}\\cdot\\frac{1}{3} + \\left(\\frac{2}{3}\\right)^2\\cdot\\frac{1}{3} + \\left(\\frac{2}{3}\\right)^3\\cdot\\frac{1}{3} + \\left(\\frac{2}{3}\\right)^4\\cdot\\frac{1}{3}.$$\nThis is\n$$\\frac{\\frac{1}{3}\\left(1-\\left(\\frac{2}{3}\\right)^5\\right)}{1-\\frac{2}{3}} = 1 - \\left(\\frac{2}{3}\\right)^5 = 1 - \\frac{32}{243} = \\frac{211}{243}.$$\nFinal Answer: \\boxed{\\frac{211}{243}}",
        ),
        (
            "What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?",
            "Move all terms to one side: $x^2 + 14x + y^2 - 4y = 10$. Completing the square gives $(x+7)^2 + (y-2)^2 = 63$, so the region is a circle with radius $\\sqrt{63}$. Its area is $\\pi r^2 = 63\\pi$.\nFinal Answer: \\boxed{63\\pi}",
        ),
        (
            "If $x^2+y^2=1$, what is the largest possible value of $|x|+|y|$?",
            "By symmetry we may assume $x, y \\ge 0$, so we maximize $x + y$ subject to $x^2 + y^2 = 1$. Then\n$$(x+y)^2 = x^2 + 2xy + y^2 = 1 + 2xy.$$\nBecause $(x-y)^2 \\ge 0$, we have $x^2 + y^2 \\ge 2xy$, so $1 \\ge 2xy$. Therefore $(x+y)^2 \\le 2$, hence $x+y \\le \\sqrt{2}$. Equality occurs at $x=y=\\frac{1}{\\sqrt{2}}$.\nFinal Answer: \\boxed{\\sqrt{2}}",
        ),
        (
            "If $f(x)=\\frac{ax+b}{cx+d}, abcd\\not=0$ and $f(f(x))=x$ for all $x$ in the domain of $f$, what is the value of $a+d$?",
            "If $f(f(x)) = x$, then $f$ is its own inverse, so its graph is symmetric about the line $y=x$. The vertical asymptote is $x = -\\frac{d}{c}$ and the horizontal asymptote is $y = \\frac{a}{c}$. Their intersection must lie on $y=x$, so $-\\frac{d}{c} = \\frac{a}{c}$. Hence $a = -d$, giving $a+d = 0$.\nFinal Answer: \\boxed{0}",
        ),
        (
            "Expand $(2z^2 + 5z - 6)(3z^3 - 2z + 1)$.",
            "Distribute each term:\n$2z^2(3z^3 - 2z + 1) = 6z^5 - 4z^3 + 2z^2$,\n$5z(3z^3 - 2z + 1) = 15z^4 - 10z^2 + 5z$,\n$-6(3z^3 - 2z + 1) = -18z^3 + 12z - 6$.\nAdding like terms gives $6z^5 + 15z^4 - 22z^3 - 8z^2 + 17z - 6$.\nFinal Answer: \\boxed{6z^5+15z^4-22z^3-8z^2+17z-6}",
        ),
    ]
    examples["math-tora"] = [
        (
            "Convert the point $(0, -3 \\sqrt{3}, 3)$ in rectangular coordinates to spherical coordinates. Enter your answer in the form $(\\rho,\\theta,\\phi)$, where $\\rho > 0$, $0 \\le \\theta < 2\\pi$, and $0 \\le \\phi \\le \\pi$.",
            "```python\nfrom sympy import acos, atan2, sqrt\n\nx, y, z = 0, -3 * sqrt(3), 3\nrho = sqrt(x**2 + y**2 + z**2)\ntheta = atan2(y, x)\nphi = acos(z / rho)\nprint((rho, theta, phi))\n```\n```output\n(6, -pi/2, pi/3)\n```\nFinal Answer: \\boxed{(6, \\frac{3\\pi}{2}, \\frac{\\pi}{3})}",
        ),
        (
            "Compute $1011_2 + 101_2 - 1100_2 + 1101_2$. Express your answer in base 2.",
            "```python\ndef binary_sum_diff():\n    num1 = int(\"1011\", 2)\n    num2 = int(\"101\", 2)\n    num3 = int(\"1100\", 2)\n    num4 = int(\"1101\", 2)\n    result = num1 + num2 - num3 + num4\n    return format(result, \"b\")\n\nanswer = binary_sum_diff()\nprint(answer)\n```\n```output\n10001\n```\nFinal Answer: \\boxed{10001_2}",
        ),
        (
            "Find the matrix that corresponds to projecting onto the vector $\\begin{pmatrix} 2 \\\\ -3 \\end{pmatrix}.$",
            "```python\nfrom sympy import Matrix\n\nv = Matrix([2, -3])\nprint((v * v.T) / (v.T * v)[0])\n```\n```output\nMatrix([[4/13, -6/13], [-6/13, 9/13]])\n```\nFinal Answer: \\boxed{\\begin{pmatrix} \\frac{4}{13} & -\\frac{6}{13} \\\\ -\\frac{6}{13} & \\frac{9}{13} \\end{pmatrix}}",
        ),
        (
            "Solve the inequality\n\\[\\frac{x^2 - 25}{x + 5} < 0.\\]",
            "```python\nfrom sympy import symbols\nfrom sympy.core.relational import StrictLessThan\nfrom sympy.solvers.inequalities import solve_univariate_inequality\n\nx = symbols(\"x\")\nexpr = (x**2 - 25) / (x + 5)\nprint(solve_univariate_inequality(StrictLessThan(expr, 0), x, relational=False))\n```\n```output\nUnion(Interval.open(-oo, -5), Interval.Lopen(-5, 5))\n```\nFinal Answer: \\boxed{(-\\infty,-5)\\cup(-5,5)}",
        ),
        (
            'In the figure, triangles $ABC$ and $BCD$ are equilateral triangles. What is the value of $AD \\div BC$ when expressed in simplest radical form?\n\n[asy]\ndraw((0,0)--(5,8.7)--(10,0)--cycle);\ndraw((10,0)--(15,8.7)--(5,8.7));\nlabel("$A$",(0,0),SW);\nlabel("$B$",(5,8.7),N);\nlabel("$C$",(10,0),SE);\nlabel("$D$",(15,8.7),NE);\n[/asy]',
            "```python\nfrom sympy import sqrt\n\nprint(sqrt(3))\n```\n```output\nsqrt(3)\n```\nFinal Answer: \\boxed{\\sqrt{3}}",
        ),
    ]
    return examples


def get_few_shot_examples(dataset_name: str | None) -> List[Example]:
    """Return few-shot exemplars for the target dataset."""
    dataset_name = (dataset_name or "").lower()
    examples = get_examples()
    if "gsm" in dataset_name:
        return list(examples["gsm8k"])
    if "aime" in dataset_name:
        return list(examples["math"][:2] + examples["gsm8k"][:2])
    return list(examples["math"])


def get_tir_reference_examples(dataset_name: str | None) -> List[Example]:
    """Return concise TIR reference exemplars for the target dataset."""
    dataset_name = (dataset_name or "").lower()
    examples = get_examples()
    if "gsm" in dataset_name:
        return list(examples["gsm8k-tora"][:1])
    if "aime" in dataset_name:
        return list([examples["math-tora"][0], examples["gsm8k-tora"][0]])
    return list(examples["math-tora"][:1])
