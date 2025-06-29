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
    False, # Hallow
    True, # Mushroom
    False, # Universal
]

NPC_filter = [
    True, # Guide
    True, # Merchant
    True, # Zoologist
    True, # Golfer
    True, # Clothier
    True, # Goblin Tinkerer
    True, # Demolitionist
    False, # Steampunker
    True, # Arms Dealer
    True, # Dye Trader
    True, # Stylist
    True, # Angler
    False, # Pirate
    False, # Tax Collector
    False, # Cyborg
    True, # Mechanic
    True, # Witch Doctor
    True, # Dryad
    True, # Painter
    True, # Nurse
    True, # Tavernkeep
    False, # Wizard
    True, # Party Girl
    False, # Truffle
    False, # Santa Claus
    False, # Princess
]

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
model = gp.Model("npc_happiness_linear")

# j in {0, ..., i} to remove duplicates (x_{n,m,b} = x_{m,n,b})
tl = gp.tuplelist((i,j,k) for i in NPCS for j in range(i+1) for k in BIOMES)

# decision variables (binary)
# x[m,n,b]:
#   m=n: NPC n lives in biome b 
#   m!=n: NPC m and n live in biome b
x = model.addVars(tl, vtype=GRB.BINARY)

# objective function
c = np.zeros((NUM_NPCS, NUM_NPCS, NUM_BIOMES))
for i, j, k in tl:
    if i == j:
        c[i,j,k] = biomePrefs[i,k]
    else:
        c[i,j,k] = neighborPrefs[i,j] + neighborPrefs[j,i]

objective = gp.quicksum(c[t] * x[t] for t in tl)

# constraints
constraints = []

one_biome_per_npc = model.addConstrs((gp.quicksum(x[n,n,b] for b in BIOMES) == 1 for n in NPCS), name = "one_biome_per_npc")

max_npcs_per_biome = model.addConstrs((gp.quicksum(x[n,n,b] for n in NPCS) <= 3 for b in BIOMES), name = "max_npcs_per_biome")

# optional due to town pets
# min_npcs_per_biome = model.addConstrs((gp.quicksum(x[n,n,b] for n in NPCS) >= 2 for b in BIOMES), name = "min_npcs_per_biome")

linearize_1 = model.addConstrs((x[m,n,b] <= x[m,m,b] for m,n,b in tl if m != n), name = "linearize_1")
linearize_2 = model.addConstrs((x[m,n,b] <= x[n,n,b] for m,n,b in tl if m != n), name = "linearize_2")
linearize_3 = model.addConstrs((x[m,n,b] >= x[m,m,b] + x[n,n,b] - 1 for m,n,b in tl if m != n), name = "linearize_3")

# account for universal pylon if needed
u_biome = None
u_bilinear = None
if "Universal" in BIOME_NAMES:
    u_biome = model.addVars((b for b in BIOMES[:-1]), vtype=GRB.BINARY)
    u_bilinear = model.addVars(((n, b) for n in NPCS for b in BIOMES[:-1]), vtype=GRB.BINARY)
    u_biome_con = model.addConstr(gp.quicksum(u_biome[b] for b in BIOMES[:-1]) == 1, name = "u_biome")
    u_lin_1 = model.addConstrs((u_bilinear[n,b] <= u_biome[b] for n in NPCS for b in BIOMES[:-1]), name = "u_lin_1")
    u_lin_2 = model.addConstrs((u_bilinear[n,b] <= x[n,n,BIOMES[-1]] for n in NPCS for b in BIOMES[:-1]), name = "u_lin_2")
    u_lin_3 = model.addConstrs((u_bilinear[n,b] >= u_biome[b] + x[n,n,BIOMES[-1]] - 1 for n in NPCS for b in BIOMES[:-1]), name = "u_lin_3")
    objective += gp.quicksum(biomePrefs[n,b] * u_bilinear[n,b] for n in NPCS for b in BIOMES[:-1])

# optimize
model.setObjective(objective, GRB.MAXIMIZE)

model.optimize()

# results
living_assignments = {b: set() for b in BIOMES}
for n in NPCS:
    n_biome = [b for b in BIOMES if x[n,n,b].X == 1][0]
    living_assignments[n_biome].add(n)

for k,v in living_assignments.items():
    print(f"{BIOME_NAMES[k]}: {list(map(lambda n: NPC_NAMES[n], v))}")

if "Universal" in BIOME_NAMES:
    print(f"Universal Pylon is in the {BIOME_NAMES[[k for k, v in u_biome.items() if v.X == 1][0]]} biome.")

# print(f"Obj: {model.ObjVal:g}")