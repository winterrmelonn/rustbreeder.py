# Salutations.
# Today(s), we'll be replicating a site called rustbreeder.com.
# In Rust, there are advantageous teas that can be made with berries. By crossbreeding berry seeds, you can obtain seeds with faster growing times and greater yields.
# Each seed has 6 gene slots. The goal here: grow our own GGGYYY clone.

# Step 1: Create User Input (you need to have seeds to crossbreed after all)

user_input_plants = []
while True:
    user_input = input("Add gene:").upper()
    letters_in_genepool = True
    for letter_input in user_input:
      if letter_input not in "GYHXW":
        letters_in_genepool = False
    if not letters_in_genepool:
      print("Invalid gene.")
      continue
    if user_input == "":
     print("Entered genes:", user_input_plants)
     break
    if len(user_input) != 6:
     print("Invalid gene.")
     continue
    user_input_plants.append(user_input)

# The user inputs gene combinations that are added to a table.
# I've coded in checks to ensure user input is 6 letters long and follows Rust's gene conventions. (GYHWX, representing Growth, Yield, Hardiness, Water, and Nothing, respectively.)
# User inputs that fail the checks are not added to the table. Lowercase inputs are automatically uppercased.

# Step 2: Counting & Scoring

def score(single_plant):
  count_G = single_plant.count("G")
  count_Y = single_plant.count("Y")
  count_H = single_plant.count("H")
  return (count_G * 10) + (count_Y * 10) + (count_H * 2) + (min (count_G, count_Y) * 5)
for single_plant in user_input_plants:
  print(single_plant, score(single_plant))

# Some genes, like Growth and Yield, are more desirable than others: let's weigh each gene; a high score for Growth and Yield genes, zero score for Water and Nothing genes, and weigh Haridiness between the two.
# We use the minimum function to accomodate balance. We want a balance of Growth and Yield genes.
# The ideal plant (3G, 3Y) will return a minimum of 3.
# Unbalanced plants, (6G, 0Y) will return a minimum of 0. We want the balance to affect plant rankings; so multiply this minimum value by 5.

best_plant = ""
best_plant_score = -1
current_score = 0

for single_plant in user_input_plants:
  current_score = score(single_plant)
  if current_score > best_plant_score:
    best_plant_score = current_score
    best_plant = single_plant
print("Best plant:", best_plant, "with score:", best_plant_score)

# Step 3: Predicting a Gene

# Rust genetics sort individually.
# Think of each of the six genes as a slot.
# We can calculate each slot outcome of a plant given its "slot neighbors." (the gene of a neighboring plant(s) at that slot)

slot_weights = {"G": 0, "Y": 0, "H": 0, "W": 0, "X": 0} # Create a dictionary to associate values with each gene.
neighbors_for_slot = ["G", "Y", "Y", "Y"]
current_letter = "" # Loop variable.

for current_letter in neighbors_for_slot:
  if current_letter in "GYH":
    slot_weights[current_letter] += 3 # Green genes (GYH) are weighted as 0.6 (we're using a scale of 10).
  else:
    slot_weights[current_letter] += 5 # Red genes (WX) are weighted as 1. Two green genes are needed to outbreed a red gene.
print("Slot weights:", slot_weights)

# The gene with the highest "weight" will be inherited by the offspring.
# Now that we have all of the weights, we need to identify which gene has the highest weight.

winner_single_gene = ""
current_gene = "" # Loop variable.
winning_neighbor_gene = ""
neighbor_slot_weight = -1

for current_gene in slot_weights:
  if slot_weights[current_gene] > neighbor_slot_weight:
    neighbor_slot_weight = slot_weights[current_gene]
    winning_neighbor_gene = current_gene

center_plant_single_gene = "X" # Define center gene.
center_slot_weight = ""

if center_plant_single_gene in "GYH":
  center_slot_weight = 3
else:
  center_slot_weight = 5

if neighbor_slot_weight > center_slot_weight:
  winner_single_gene = winning_neighbor_gene
else:
  winner_single_gene = center_plant_single_gene
print(winner_single_gene)

# Step 4: Predicting a Plant

center_plant = "XYGWGG"
neighbor_plants = ["GGGGGG", "GGGGGG"]
offspring = ""

for slots in range(6):
  slot_weights = {"G": 0, "Y": 0, "H": 0, "W": 0, "X": 0} # Reset weighting system for each slot.
  center_plant_single_gene = center_plant[slots]

  neighbors_for_slot = []
  for neighbor_plant in neighbor_plants:
    neighbors_for_slot.append(neighbor_plant[slots])
# Copy and paste Step 3 slot weight counter.
  for current_letter in neighbors_for_slot:
    if current_letter in "GYH":
      slot_weights[current_letter] += 3
  else:
    slot_weights[current_letter] += 5
# Copy and paste loop to find heaviest gene & winner gene.
  for current_gene in slot_weights:
    if slot_weights[current_gene] > neighbor_slot_weight:
      neighbor_slot_weight = slot_weights[current_gene]
    winning_neighbor_gene = current_gene
    if center_plant_single_gene in "GYH":
      center_slot_weight = 3
    else:
      center_slot_weight = 5
    if neighbor_slot_weight > center_slot_weight:
      winner_single_gene = winning_neighbor_gene
    else:
      winner_single_gene = center_plant_single_gene
  offspring = offspring + winner_single_gene

print("Offspring:", offspring)
