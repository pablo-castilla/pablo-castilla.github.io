import gurobipy as gp
from gurobipy import GRB
import numpy as np

BIOME_NAMES = [
    "Forest",
    "Cavern",
    "Desert",
    "Ocean",
    "Snow",
    "Jungle",
    "Hallow",
    "Mushroom",
    "Universal", # UNIVERSAL MUST BE THE LAST BIOME IN THE LIST
]

NPC_NAMES = [
    "Guide",
    "Merchant",
    "Zoologist",
    "Golfer",
    "Clothier",
    "Goblin Tinkerer",
    "Demolitionist",
    "Steampunker",
    "Arms Dealer",
    "Dye Trader",
    "Stylist",
    "Angler",
    "Pirate",
    "Tax Collector",
    "Cyborg",
    "Mechanic",
    "Witch Doctor",
    "Dryad",
    "Painter",
    "Nurse",
    "Tavernkeep",
    "Wizard",
    "Party Girl",
    "Truffle",
    "Santa Claus",
    "Princess",
]

biomePrefs = np.matrix([
    # F  C  D  O  S  J  H  M  U
    [ 1, 0, 0,-1, 0, 0, 0, 0, 0,], # Guide
    [ 1, 0,-1, 0, 0, 0, 0, 0, 0,], # Merchant
    [ 1, 0,-1, 0, 0, 0, 0, 0, 0,], # Zoologist
    [ 1,-1, 0, 0, 0, 0, 0, 0, 0,], # Golfer
    [ 0, 1, 0, 0, 0, 0,-1, 0, 0,], # Clothier
    [ 0, 1, 0, 0, 0,-1, 0, 0, 0,], # Goblin Tinkerer
    [ 0, 1, 0,-1, 0, 0, 0, 0, 0,], # Demolitionist
    [ 0, 0, 1, 0, 0,-1, 0, 0, 0,], # Steampunker
    [ 0, 0, 1, 0,-1, 0, 0, 0, 0,], # Arms Dealer
    [-1, 0, 1, 0, 0, 0, 0, 0, 0,], # Dye Trader
    [ 0, 0, 0, 1,-1, 0, 0, 0, 0,], # Stylist
    [ 0, 0,-1, 1, 0, 0, 0, 0, 0,], # Angler
    [ 0,-1, 0, 1, 0, 0, 0, 0, 0,], # Pirate
    [ 0, 0, 0, 0, 1, 0,-1, 0, 0,], # Tax Collector
    [ 0, 0, 0, 0, 1,-1, 0, 0, 0,], # Cyborg
    [ 0,-1, 0, 0, 1, 0, 0, 0, 0,], # Mechanic
    [ 0, 0, 0, 0, 0, 1,-1, 0, 0,], # Witch Doctor
    [ 0, 0,-1, 0, 0, 1, 0, 0, 0,], # Dryad
    [-1, 0, 0, 0, 0, 1, 0, 0, 0,], # Painter
    [ 0, 0, 0, 0,-1, 0, 1, 0, 0,], # Nurse
    [ 0, 0, 0, 0,-1, 0, 1, 0, 0,], # Tavernkeep
    [ 0, 0, 0,-1, 0, 0, 1, 0, 0,], # Wizard
    [ 0,-1, 0, 0, 0, 0, 1, 0, 0,], # Party Girl
    [ 0, 0, 0, 0, 0, 0, 0, 1, 0,], # Truffle
    [ 0, 0,-2, 0, 2, 0, 0, 0, 0,], # Santa Claus
    [ 0, 0, 0, 0, 0, 0, 0, 0, 0,], # Princess
])

neighborPrefs = np.matrix([
    # G  M  Z  G  C  G  D  S  A  D  S  A  P  T  C  M  W  D  P  N  T  W  P  T  S  P
    [ 0, 0, 1, 0, 1, 0, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-2, 0, 0, 0, 0, 0, 0, 1,], # Guide
    [ 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,-2, 0,-1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1,], # Merchant
    [ 0, 0, 0, 1, 0, 0, 0, 0,-2, 0, 0,-1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Zoologist
    [ 0,-2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2,-1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,], # Golfer
    [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-0, 0, 2, 0, 0, 0,-1, 0, 0, 0, 1, 0, 1,], # Clothier
    [ 0, 0, 0, 0,-1, 0, 0, 0, 0, 1,-2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Goblin Tinkerer
    [ 0, 0, 0, 0, 0,-1, 0, 0,-1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1,], # Demolitionist
    [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0,-1, 1, 0, 0,-1,-1, 0, 0, 1,], # Steampunker
    [ 0, 0, 0,-1, 0, 0,-2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 1,], # Arms Dealer
    [ 0, 0, 0, 0, 0, 0, 0,-1, 1, 0, 0, 0,-2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,], # Dye Trader
    [ 0, 0, 0, 0, 0,-2, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,-1, 0, 0, 0, 0, 1,], # Stylist
    [ 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,-2, 0, 1, 0, 0, 1,], # Angler
    [-2, 0, 0, 0, 0, 0, 0, 0, 0, 0,-1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,], # Pirate
    [ 0, 2, 0, 0, 0, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0,-1, 0, 0, 0, 0, 0, 0, 1, 0,-2, 1,], # Tax Collector
    [ 0, 0,-1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,-2, 0, 0, 0, 1,], # Cyborg
    [ 0, 0, 0, 0,-2, 2, 0, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Mechanic
    [ 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,-1, 0, 0, 0,-2, 0, 1,], # Witch Doctor
    [ 0, 0, 0,-2, 0, 0, 0, 0, 0, 0, 0,-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1,], # Dryad
    [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-1, 0, 0, 2, 0, 0, 0, 0, 1,-1, 0, 1,], # Painter
    [ 0, 0,-2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,-1, 0, 0, 0, 1,-1, 0, 0, 1,], # Nurse
    [-1, 0, 0, 0, 0, 1, 2, 0, 0,-2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Tavernkeep
    [ 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-2, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Wizard
    [ 0,-1, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,-2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1,], # Party Girl
    [ 2, 0, 0, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-2, 1, 0, 0, 0, 0, 0, 0, 0, 1,], # Truffle
    [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,], # Santa Claus
    [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0,], # Princess
])

# ---------------- INPUT SETTINGS ----------------
# filter out unwanted NPCs / biomes
# True = to be removed
BIOME_filter = [
    True, # Forest
    True, # Cavern
    True, # Desert
    True, # Ocean
    True, # Snow
    True, # Jungle
    True, # Hallow
    True, # Mushroom
    True, # Universal
]

# (H) = Hardmode only
NPC_filter = [
    True, # Guide
    True, # Merchant
    True, # Zoologist
    True, # Golfer
    True, # Clothier
    True, # Goblin Tinkerer
    True, # Demolitionist
    True, # Steampunker (H)
    True, # Arms Dealer
    True, # Dye Trader
    True, # Stylist
    True, # Angler
    True, # Pirate (H)
    True, # Tax Collector (H)
    True, # Cyborg (H)
    True, # Mechanic
    True, # Witch Doctor
    True, # Dryad
    True, # Painter
    True, # Nurse
    True, # Tavernkeep
    True, # Wizard (H)
    True, # Party Girl
    True, # Truffle (H)
    True, # Santa Claus (H)
    True, # Princess (H)
]

count_all_solns = False
# ------------------------------------------------

BIOME_NAMES = [name for i, name in enumerate(BIOME_NAMES) if BIOME_filter[i]]
NPC_NAMES = [name for i, name in enumerate(NPC_NAMES) if NPC_filter[i]]

biomePrefs = np.delete(biomePrefs, [i for i,n in enumerate(NPC_filter) if not n], 0)
biomePrefs = np.delete(biomePrefs, [i for i,b in enumerate(BIOME_filter) if not b], 1)

neighborPrefs = np.delete(neighborPrefs, [i for i,n in enumerate(NPC_filter) if not n], 0)
neighborPrefs = np.delete(neighborPrefs, [i for i,n in enumerate(NPC_filter) if not n], 1)

print(np.shape(biomePrefs))
print(np.shape(neighborPrefs))
print(BIOME_NAMES)
print(NPC_NAMES)

NUM_NPCS = len(NPC_NAMES)
NUM_BIOMES = len(BIOME_NAMES)

NPCS = range(NUM_NPCS)
BIOMES = range(NUM_BIOMES)

print(NUM_NPCS, NUM_BIOMES)

# initialize model
model = gp.Model("npc_happiness_nonlinear")

# j in {0, ..., i} to remove duplicates (x_{n,m,b} = x_{m,n,b})
tl = gp.tuplelist((n,b) for n in NPCS for b in BIOMES)

# decision variables (binary)
# x[m,n,b]:
#   m=n: NPC n lives in biome b 
#   m!=n: NPC m and n live in biome b
x = model.addVars(tl, vtype=GRB.BINARY)

# objective function
objective = gp.quicksum(
    x[n,b] * (
        biomePrefs[n,b] + gp.quicksum (x[m,b] * neighborPrefs[n,m] for m in NPCS)
    ) for n in NPCS for b in BIOMES
)

# constraints
constraints = []

one_biome_per_npc = model.addConstrs((gp.quicksum(x[n,b] for b in BIOMES) == 1 for n in NPCS), name = "one_biome_per_npc")

max_npcs_per_biome = model.addConstrs((gp.quicksum(x[n,b] for n in NPCS) <= 3 for b in BIOMES), name = "max_npcs_per_biome")

# optional due to town pets
# min_npcs_per_biome = model.addConstrs((gp.quicksum(x[n,b] for n in NPCS) >= 2 for b in BIOMES), name = "min_npcs_per_biome")

# account for universal pylon if needed
u = None
if "Universal" in BIOME_NAMES:
    u = model.addVars((b for b in BIOMES[:-1]), vtype=GRB.BINARY)
    one_u_biome = model.addConstr(gp.quicksum(u[b] for b in BIOMES[:-1]) == 1, name = "one_u_biome")
    objective += gp.quicksum(biomePrefs[n,b] * u[b] * x[n,BIOMES[-1]] for n in NPCS for b in BIOMES[:-1])

# optimize
model.setObjective(objective, GRB.MAXIMIZE)

if count_all_solns:
    model.setParam(GRB.Param.PoolSolutions, 1024)
    model.setParam(GRB.Param.PoolGap, 0)
    model.setParam(GRB.Param.PoolSearchMode, 2)

model.optimize()

# results
living_assignments = {b: set() for b in BIOMES}
for n in NPCS:
    n_biome = [b for b in BIOMES if x[n,b].X == 1][0]
    living_assignments[n_biome].add(n)

for k,v in living_assignments.items():
    print(f"{BIOME_NAMES[k]}: {list(map(lambda n: NPC_NAMES[n], v))}")

if "Universal" in BIOME_NAMES:
    print(f"Universal Pylon is in the {BIOME_NAMES[[k for k, v in u.items() if v.X == 1][0]]} biome.")

if count_all_solns:
    print(f"Number of solutions found: {model.SolCount}")