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
I hope this provides a model for an approachable beginner discrete optimization project.

## Terraria, NPCs, and Happiness
The video game *Terraria* has 26 unique town NPCs that can live in your world.
Most NPCs are vendors which buy and sell items to players.

Each NPC has a happiness modifier which is applied as a percent discount to the items it sells to the player.
(Lower is better!)
The modifier's inverse is applied for the NPCs buying items from the players.
From the [Official Terraria Wiki](https://terraria.wiki.gg/wiki/NPCs#Happiness), the modifider starts at 1 is calculated as follows:

1. **Solitude Bonus:** If there are no more than two other NPCs within 25 tiles and no more than three other NPCs between 25 and 120 tiles away, multiply by 95%.
2. **Crowded Penalty:** For each other NPC within 25 tiles after the third, multiply by 105%.
3. If the NPC is in a biome it loves/likes/dislikes/hates, multiply by 88%/94%/106%/112% respectively.
4. For each other NPC within 25 tiles, if the NPC loves/likes/dislikes/hates them, multiply by 88%/94%/106%/112% respectively.
5. Round to the nearest 1% increment and cap the multiplier at a minimum of 67% and a maximum of 133%.

The goal is to optimize the overall happiness of the NPCs!

## The Model
Let's put the NPCs into groups where NPCs within a group are all within 25 tiles of each other and each group is in a different biome.
This is the most common setup in gameplay due to [pylons](https://terraria.wiki.gg/wiki/Pylons), teleport points that can be set up once in each biome.
Not only is this a convenient setup for the player to access all their NPCs, but pylons require at least two nearby NPCs (or town pets) to be active.
We will limit each group to be at most three NPCs, so they all benefit from the solitude bonus.
If the player wants to ignore town pets while maintiaining activated pylons, a minimum of two NPCs per pylon can also be enforced.

Now, let's model the multiplicative happiness modifier with a much simpler additive score.
We can ignore the crowded penalty and solitude bonus since we are guaranteeing each NPC has at most two neighbors.

1. NPC happiness starts at 0.
2. Add +2/+1/0/-1/-2 depending on the NPC's biome preference.
3. For each other NPC in its group, add +2/+1/0/-1/-2 depending on the NPC's preference for them as its neighbor.

Here, a higher happiness score is better.
This additive model is a great approximation to the in-game modifier (up to some constant factor, of course.)
Now, we can maximize the sum of our NPC's happiness scores.

## Building the Program
Let $$N$$ be the set of NPCs and $$B$$ be the set of biomes.
Our data will be in two matrices:

- $$BP$$: an $$\vert N \vert \times \vert B \vert$$ matrix, where $$BP_{n,b}$$ is NPC $$n$$'s preference for biome $$b$$.
- $$NP$$: an $$\vert N \vert \times \vert N \vert$$ matrix, where $$BP_{n,m}$$ is NPC $$n$$'s preference for being neighbors with NPC $$m$$.

To encode where each NPC lives, we have binary decision variables $$x_{n,b}$$ for $$(n,b) \in N \times B$$ which respresent if NPC $$n$$ lives in biome $$b$$.
Since each NPC lives in exactly one biome, we get the constraints

$$
\sum_{b \in B} x_{n,b} = 1 \quad \forall n \in N.
$$

Additionally, each biome contains at most three NPCs, leading to the constraints below.

$$
\sum_{n \in N} x_{n,b} \leq 3 \quad \forall b \in B.
$$

Finally, let's build the objective function, which will be the sum of the NPC's happiness scores.
An NPC $$n$$ recieves $$BP_{n,b}$$ happiness from living in biome $$b$$.
Since $$x_{n,b}$$ is 1 iff $$n$$ lives in biome $$b$$ and 0 otherwise, the sum

$$
  \sum_{b \in B} BP_{n,b} x_{n,b}
$$

is exactly the happiness $$n$$ gets from its biome.
Similarly, $$n$$ receives $$NP_{n,m}$$ happiness for each of its neighbors.
NPC $$m$$ is a neighbor of $$n$$ if there exists a biome $$b$$ such that $$x_{n,b} = x_{m,b} = 1$$.
Thus $$\sum_{b \in B} x_{n,b} x_{m,b} = 1$$ if $$m$$ and $$n$$ are neighbors and 0 otherwise, so $$n$$'s happiness from neighbors is

$$
  \sum_{m \in N} NP_{n,m} \sum_{b \in B} x_{n,b} x_{m,b}.
$$

Putting these two together gives us the happiness of NPC $$n$$, and summing over all NPCs results in the following objective function.

$$
\sum_{n \in N} \left(\sum_{b \in B} BP_{n,b} x_{n,b} +  \sum_{m \in N} NP_{n,m} \sum_{b \in B} x_{n,b} x_{m,b} \right)
$$

Putting it all together, we get the integer program below.

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
With our current model, this is necessary to model the endgame since *Terraria* has 26 NPCs and only 8 biomes.

To add a new NPC group, let's add a new biome $$u$$ to the biome set $$B$$ that every NPC is ambivalent to.
This way, our current objective function accounts for the happiness scores of NPCs in the universal pylon group from their neighbors and we just have to add the happiness they get from their biome.

To do so requires keeping track of which biome the universal pylon is in. I added binary decision variables $$x_{b}$$ for each $$b \in B \setminus \{u\}$$, where $$x_{b} = 1$$ if the universal pylon is in biome $$b$$ and 0 otherwise.
The universal pylon exists in exactly one biome, so we add the constraint

$$
\sum_{b \in B \setminus \{u\}} x_{b} = 1.
$$

Each NPC $$n$$ in the universal pylon group then gets happiness $$\sum BP_{n,b} x_{b}$$ from its biome, so the total happiness the NPCs in the universal pylon group get from their biome is

$$
  \sum_{n \in N} x_{n,u} \sum_{b \in B \setminus \{u\}} BP_{n,b} x_{b}.
$$

Add this term to the objective function then updates it to account for the universal pylon group.
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
I decided to implement it and compare its performance in Gurobi versus the bilinear formulation above.

For two decision variables $$x_1, x_2$$, the expression $$x_1 x_2$$ can be linearized by creating a new binary decision variable $$x_3$$ and adding the following constraints:

$$
x_3 \geq x_1 \\
x_3 \geq x_2 \\
x_3 \leq x_1 + x_2 - 1 \\
$$

This linearization comes at the cost of quadratically more variables and constraints: one new variable and three new constraints for each bilinear term.

Ignoring the universal pylon for now, the bilinear terms in our objective function are all of the form $$x_{n,b} x_{m,b}$$ for each $$n,m \in N$$ and $$b \in B$$.
To linearize, we create a decision variable $$x_{n,m,b} := x_{n,b} x_{m,b}$$ that represents if both $$n$$ and $$m$$ live in biome $$b$$.
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

Note that $$x_{n,m,b} = x_{m,n,b}$$, so we end up with a total of $$(\vert N \vert+1) \cdot \vert N \vert \cdot \vert B \vert$$ decision variables.

In the case of the universal pylon, we can linearize the $$x_{n,u} x_{b}$$ terms by adding decision variables $$x_{n,u,b} := x_{n,u} x_{b}$$ for each $$n \in N$$ and $$b \in B \setminus \{u\}$$, where $$x_{n,u,b} = 1$$ iff $$n$$ is is biome $$u$$ and the universal pylon is in biome $$b$$.
Then, the extra term in the objective function is

$$
\sum_{n \in N} \sum_{b \in B \setminus u} BP_{n,b} x_{n,u,b}
$$

and we must add the three constraints below.

$$
\begin{align*}
x_{n,u,b} &\geq x_{n,u} & \forall n \in N \\
x_{n,u,b} &\geq x_{b} & \forall b \in B \setminus \{u\} \\
x_{n,u,b} &\leq x_{n,u} + x_{b} - 1 & \forall n \in N, b \in B \setminus \{u\} \\
\end{align*}
$$

## Results
I wrote two python programs, [one with the original nonlinear formulation](/_posts/terraria_NPCs_nonlinear.py) and one with the [linearized formulation](/_posts/terraria_NPCs_nonlinear.py).

I ran each on two scenarios: all the NPCs and biomes the player can access in Pre-Hardmode (before defeating the [Wall of Flesh](https://terraria.wiki.gg/wiki/Wall_of_Flesh)) and the endgame where the player has access to every NPC and biome.

The results for each are in the table below.
The solution time is measured in work units, a deterministic unit of computation roughly equivalent to seconds of compute time.

|Scenarios   |NPCs|Biomes|Nonlinear Formulation Time (work units)|Linear Formulation Time (work units)|
|:----------:|:--:|:----:|:-------------------------------------:|:----------------------------------:|
|Pre-hardmode|18  |7     |0.05                                   |0.04                                |
|Endgame     |26  |9     |2.93                                   |1.82                                |

Surprise surprise, my linear reformulation is not as good as Gurobi!
This really should not be a surprise; applying this trick was helpful for performance, Gurobi would be doing it already and better than my manual implementation.
Also, the size of this problem is tiny in the context of discrete optimization, so take these with a grain of salt.

And in terms of the number of optimal solutions, my code found 13 optimal solutions for the pre-hardmode scenario and 722 solutions for the endgame scenario.
Note that the endgame scenario solutions are duplicated, as the NPCs in the universal pylon group could be swapped with the NPCs in appropriate biome, so there are more like 361 solutions.
Even so, I expected far fewer optimal solutions than 722, but remember there are $$9 \cdot \binom{26}{3, \dots, 3, 2} \approx 10^{21}$$ total arrangements!

And *Terraria* players, I won't leave you hanging.
Here is one solution of each scenario.

### Optimal Pre-Hardmode Solution (Objective Value: 35)
|Biome       |NPCs                               |
|:----------:|:---------------------------------:|
|Forest      |Guide, Zoologist, Golfer           |
|Cavern      |Tavernkeep, Clothier, Demolitionist|
|Desert      |Dye Trader                         |
|Ocean       |Stylist, Angler, Party Girl        |
|Snow        |Mechanic, Goblin Tinkerer          |
|Jungle      |Witch Doctor, Dryad, Painter       |
|Hallow      |Merchant, Nurse, Arms Dealer       |
|Mushroom    |None                               |

### Optimal Endgame Solution (Objective Value: 54)
|Biome             |NPCs                                  |
|:----------------:|:------------------------------------:|
|Forest            |Zoologist, Golfer, Party Girl         |
|Cavern            |Clothier, Tavernkeep, Demolitionist   |
|Desert            |Stylist, Cyborg, Steampunker          |
|Ocean             |Angler, Pirate, Tax Collector         |
|Snow              |Santa Claus, Goblin Tinkerer, Mechanic|
|Jungle            |Witch Doctor, Dryad, Painter          |
|Hallow            |Merchant, Wizard                      |
|Mushroom          |Guide, Princess, Truffle              |
|Universal (Desert)|Arms Dealer, Dye Trader, Nurse        |


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