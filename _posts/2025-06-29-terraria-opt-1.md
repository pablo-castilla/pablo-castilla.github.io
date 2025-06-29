---
title: 'Optimizing Terraria NPC Placements'
date: 2025-06-29
permalink: /posts/2025/06/terraria-optimization-1/
tags:
  - discrete optimization
  - video games
---

# Optimizing Terraria NPC Placements
A while ago, I wrote an integer program to optimize the placement of NPCs in Terraria using [CVXPY](https://www.cvxpy.org/).
I recently rewrote it using [gurobipy](https://pypi.org/project/gurobipy/) and decided it's worth writing a small article about the process.
The project is a great example of an approachable beginner discrete optimization project.

## Terraria, NPCs, and Happiness
The video game *Terraria* has 26 unique town NPCs that can live in your world.
Most NPCs are vendors which buy and sell items to players.

Each NPC has a happiness modifier, which affects the price it sells its items for and how much it will pay for the player's items.
From the [Official Terraria Wiki](https://terraria.wiki.gg/wiki/NPCs#Happiness), the modifider is calculated as follows:

1. The default happiness modifier is 1.
2. **Solitude Bonus:** If there are no more than two other NPCs within 25 tiles and no more than three other NPCs between 25 and 120 tiles away, multiply by 105%.
3. **Crowded Penalty:** For each other NPC within 25 tiles after the third, multiply by 95%.
4. If the NPC is in a biome it loves/likes/dislikes/hates, multiply by 114%/106%/94%/89% respectively.
5. For each other NPC within 25 tiles, if the NPC loves/likes/dislikes/hates them, multiply by 114%/106%/94%/89% respectively.
6. Round to the nearest 1% increment, and cap the multiplier at a minimum of 67% and a maximum of 133%.

This modifier is applied to the value of items the NPC buys from the player; the modifier's recirpocal, rounded to the nearest 1% increment, is applied to the price of items the NPC sells to the player. **We are going to optimize the total happiness of our NPCs.**

## The Model
Firstly, we will assume NPCs live in groups where all NPCs in a group live in the same biome and each NPC is within 25 tiles of each other NPC in their group.
We will constrain each NPC group to have at most three NPCs, so NPCs benefit from the solitude bonus.
This is the most common setup in gameplay due to [pylons](https://terraria.wiki.gg/wiki/Pylons), teleport points that can be set up once in each biome.
Not only is this convenient, but pylons require at least two nearby NPCs (or town pets) to be active.
One may ignore town pets and constrain groups to a minimum size of two NPCs for activated pylons.

Now, let's model the multiplicative happiness modifier with a much
simpler additive modifier.
1. NPC happiness starts at 0.
2. Add +2/+1/0/-1/-2 depending on the NPC's biome preference.
3. For each other NPC in its group, add +2/+1/0/-1/-2 depending on the NPC's preference for them as its neighbor.
This additive model is a relatively good approximation to the in-game modifier up to some constant factor.

## Building the Program
Now we are ready to set up our optimization problem.
Let $N$ be the set of NPCs and $B$ be the set of biomes.
Our data will be in two matrices:

- $BP$: an $|N| \times |B|$ matrix, where $BP_{n,b}$ is NPC $n$'s preference for biome $b$.
- $NP$: an $|N| \times |N|$ matrix, where $BP_{n,m}$ is NPC $n$'s preference for being neighbors with NPC $m$.

We will have binary decision variables $x_{n,b}$ for each $n \in N$ and $b \in B$ respectively representing if NPC $n$ lives in biome $b$.
NPC $n$'s happiness changes by $BP_{n,b}$, where $b$ is the biome it lives in, so the happiness it receives from its biome is
$$
  \sum_{b \in B} BP_{n,b} x_{n,b}.
$$
It also receives $NP_{n,m}$ happiness for each of its neighbors $m$.
NPCs $n$ and $m$ are neighbors if there exists some biome $b$ such that $x_{n,b} = x_{m,b} = 1$, which is the case iff $\sum_{b \in B} x_{n,b} x_{m,b} = 1.$
Thus, $n$'s happiness from neighbors is
$$
  \sum_{m \in N} NP_{n,m} \sum_{b \in B} x_{n,b} x_{m,b}.
$$
Adding these two together gives us the happiness of an NPC $n$.
Summing over all NPC results in the following objective function.
$$
\sum_{n \in N} \left(\sum_{b \in B} BP_{n,b} x_{n,b} +  \sum_{m \in N} NP_{n,m} \sum_{b \in B} x_{n,b} x_{m,b} \right)
$$

There are two constraints: each NPC lives in exactly one biome and each biome contains at most three NPCs.
This gives us the following integer program.
$$
\begin{align*}
              \max & \sum_{n \in N} \sum_{b \in B} \left(
                        BP_{n,b} x_{n,b} + \sum_{m \in N} NP_{n,m} x_{n,b} x_{m,b}
                     \right) \\
\text{subject to } & \sum_{b \in B} x_{n,b} = 1 & \forall n \in N \\
                   & \sum_{n \in N} x_{n,b} \leq 3 & \forall b \in B \\
                   & x_{n,b} \in \{0,1\} & \forall n\in N, b \in B
\end{align*}
$$

## The Universal Pylon
The [universal pylon](https://terraria.wiki.gg/wiki/Universal_Pylon) is an additional pylon unlocked after beating the game that can be used in any biome.
Essentially, we get an extra NPC group in the biome of our choice.
With our current model, this is actually necessary since *Terraria* has 26 NPCs and only 8 biomes.

Since we are adding a new NPC group, let's add a new biome $u$ to the biome set $B$ that every NPC is ambivalent to.
This way, our current objective function accounts for the happiness of NPCs in the universal pylon group from their neighbors and we just have to add the happiness they get from their biome.

To do so requires keeping track of which biome the universal pylon is in.
Let's add binary variables $x_{b}$ for each $b \in B \setminus \{u\}$.
Each NPC $n$ in the universal pylon group respectively gets happiness $\sum BP_{n,b} x_{b}$ from its biome, so the total happiness the NPCs in the universal pylon group get from their biome is
$$
  \sum_{n \in N} x_{n,u} \sum_{b \in B \setminus \{u\}} BP_{n,b} x_{b}.
$$
This is the term we add to the objective function.

In terms of constraints, we have one additional one: the universal pylon is in exactly one biome.
$$
\sum_{b \in B \setminus \{u\}} x_{b} = 1
$$
This gives us the integer program shown below.
$$
\begin{align*}
                   \max & \sum_{n \in N} \left(
                     \sum_{b \in B} \left(
                       BP_{n,b} x_{n,b} + \sum_{m \in N} NP_{n,m} x_{n,b} x_{m,b}
                     \right)
                     + \sum_{b \in B \setminus \{u\}} BP_{n,b} x_{n,b} x_{b}
                   \right) \\
\text{subject to } & \sum_{b \in B} x_{n,b} = 1 & \forall n \in N \\
                   & \sum_{n \in N} x_{n,b} \leq 3 & \forall b \in B \\
                   & \sum_{b \in B} x_{b} = 1 \\
                   & x_{n,b}, x_{b} \in \{0,1\} & \forall n\in N, b \in B
\end{align*}
$$

## Linearization
Currently, our objective function is quadratic, which is slower to solve than if it were linear.
While doing this project, I found a trick to linearize quadratic functions of binary variables.
I decided to implement it and compare its performance in Gurobi versus the nonlinear case above.

For two decision variables $x_1, x_2$, the expression $x_1 x_2$ can be linearized by creating a new binary decision variable $x_3$ and adding the following constraints:
$$
x_3 \geq x_1 \\
x_3 \geq x_2 \\
x_3 \leq x_1 + x_2 - 1 \\
$$
This linearization comes at the cost of quadratically more variables and constraints: one new variable and three new constraints for each bilinear term.

Ignoring the universal pylon for now, the bilinear terms in our objective function are all of the form $x_{n,b} x_{m,b}$ for each $n,m \in N$ and $b \in B$.
To linearize, we create a decision variable $x_{n,m,b} := x_{n,b} x_{m,b}$ that represents if both $n$ and $m$ live in biome $b$.
Substituting our new decision variables into the objective function and adding the appropriate constraints, we get the integer program below.

$$
\begin{align*}
              \max & \sum_{n \in N} \sum_{b \in B} \left(
                        BP_{n,b} x_{n,b} + \sum_{m \in N} NP_{n,m} x_{n,m,b}
                     \right) \\
\text{subject to } & \sum_{b \in B} x_{n,b} = 1 & \forall n \in N \\
                   & \sum_{n \in N} x_{n,b} \leq 3 & \forall b \in B \\
                   & x_{n,m,b} \geq x_{n,b} & \forall n, m \in N, b \in B, n \neq m \\
                   & x_{n,m,b} \geq x_{m,b} & \forall n, m \in N, b \in B, n \neq m \\
                   & x_{n,m,b} \leq x_{n,b} + x_{m,b} - 1 & \forall n, m \in N, b \in B, n \neq m \\
                   & x_{n,b}, x_{n,m,b} \in \{0,1\} & \forall n, m \in N, b \in B
\end{align*}
$$
Note that $x_{n,m,b} = x_{m,n,b}$, so we end up with a total of $(|N|+1) \cdot |N| \cdot |B|$ decision variables.

In the case of the universal pylon, we can linearize the $x_{n,u} x_{b}$ terms by adding decision variables $x_{n,u,b} := x_{n,u} x_{b}$ for each $n \in N$ and $b \in B \setminus \{u\}$, where $x_{n,u,b} = 1$ iff $n$ is is biome $u$ and the universal pylon is in biome $b$.
Then, the extra term in the objective function is
$$
\sum_{n \in N} \sum_{b \in B \setminus u} BP_{n,b} x_{n,u,b}
$$
and we must add the constraints
$$
\begin{align*}
x_{n,u,b} &\geq x_{n,u} & \forall n \in N \\
x_{n,u,b} &\geq x_{b} & \forall b \in B \setminus \{u\} \\
x_{n,u,b} &\leq x_{n,u} + x_{b} - 1. & \forall n \in N, b \in B \setminus \{u\} \\
\end{align*}
$$

## Results
I wrote two python programs, [one with the original nonlinear formulation](/_posts/terraria_NPCs_nonlinear.py) and one with the [linearized formulation](/_posts/terraria_NPCs_nonlinear.py).

I ran each on two scenarios: all the NPCs and biomes the player can access in Pre-Hardmode (before defeating the [Wall of Flesh](https://terraria.wiki.gg/wiki/Wall_of_Flesh)) and the endgame where the player has access to every NPC and biome.

Here are the results for each:

| Scenarios    | NPCs | Biomes | Nonlinear     |Linear |
|:------------:|:----:|:------:|:-------------:|:-----:|
| Pre-hardmode | 18   | 7      | 0.05          | 0.04  |
| Endgame      | 26   | 9      | 2.93          | 1.82  |

Surprise surprise, my linear reformulation is not as good as Gurobi!
This really should not be a surprise; applying this trick was helpful for performance, Gurobi would be doing it already and better than my manual implementation.
Also, the size of this problem is tiny in the context of discrete optimization, so take these with a grain of salt.

## Discussion and Future Directions
Since NPC's homes can be changed at no cost and only one NPC is used at a time, a hardcore penny-pincher could theoretically reorganize their NPCs to maximize the happiness of whichever NPC they need to buy items from at any particular moment.
However, moving NPCs is cumbersome, and making most NPCs pretty happy is usually good enough.

There are NPCs that are used much more than others (looking at you, [Goblin Tinkerer](https://terraria.wiki.gg/wiki/Goblin_Tinkerer)) that should be prioritized in game.
This can be done in code either by weighting their happiness higher in the objective function or by enforcing their biome and neighbor preferences with constraints.

Other NPCs may never be used in play or may be need outside of the normal pylon groups.
A common example of the latter is placing the Nurse in a boss arena, allowing the player to heal during a boss fight and away from other NPCs so other NPCs are not accidentally killed.

Since the number of NPCs and biomes is very low in the context of optimization, it is feasible to calculate the optimal solution using the true NPC happiness modifier formula.
I predict that the solutions would be very close if not identical, especially in the 

I am more interested in taking the progression of the game into account when modeling the optimization problem.
This project only solves for maximum total happiness based on what NPCs and biomes a player has available to them at one point in time.
What if you wanted to, for example, maximize NPC happiness over time without ever moving NPCs?

Related to progression, a biome's pylon is unlocked when an NPC living in that biome reaches a certain threshold.
If I write a sequel article, it will be on finding out how to unlock pylons as early as possible, as they are not only useful for maximizing NPC happiness but also navigating the *Terraria* world in general.