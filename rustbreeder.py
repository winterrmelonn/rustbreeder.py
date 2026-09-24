# Salutations.
# Today(s), we'll be replicating a site called rustbreeder.com.
# In Rust, there are advantageous teas that can be made with berries. By crossbreeding berry seeds, you can obtain seeds with faster growing times and greater yields.
# Each seed has 6 gene slots. The goal here: grow our own GGGYYY clone.

GENES = "GYHXW"
WEIGHTS = {"G": 3, "Y": 3, "H": 3, "W": 5, "X": 5}  # good genes (GYH) weigh 3, bad genes (WX) weigh 5

# The breeding engine: given one plant's gene at a slot and its neighbors' genes at
# that same slot, decide which gene the offspring inherits. Ties go to the center.
def breed_slot(center_gene, neighbor_genes):
    slot_weights = {g: 0 for g in GENES}
    for gene in neighbor_genes:
        slot_weights[gene] += WEIGHTS[gene]

    winning_neighbor_gene = max(slot_weights, key=slot_weights.get)
    neighbor_slot_weight = slot_weights[winning_neighbor_gene]
    center_slot_weight = WEIGHTS[center_gene]

    if neighbor_slot_weight > center_slot_weight:
        return winning_neighbor_gene
    return center_gene

# Predict a full 6-slot offspring from a center plant and its neighbor plants.
def breed(center_plant, neighbor_plants):
    offspring = ""
    for slot in range(6):
        center_gene = center_plant[slot]
        neighbor_genes = [plant[slot] for plant in neighbor_plants]
        offspring += breed_slot(center_gene, neighbor_genes)
    return offspring

# Self-check: run this file directly to verify the engine before trusting it.
def demo():
    # one weak (3) neighbor can't beat a strong (5) center gene -> center holds
    assert breed_slot("X", ["G"]) == "X"
    # two matching good neighbors (3+3=6) beat one bad center gene (5) -> neighbor wins
    assert breed_slot("X", ["G", "G"]) == "G"
    # mixed neighbor genes never combine -> center still holds
    assert breed_slot("X", ["G", "Y"]) == "X"
    # all-G neighbors pull any center plant fully green
    assert breed("XYGWGG", ["GGGGGG", "GGGGGG"]) == "GGGGGG"
    print("demo: ok")

def score(single_plant):
  count_G = single_plant.count("G")
  count_Y = single_plant.count("Y")
  count_H = single_plant.count("H")
  return (count_G * 10) + (count_Y * 10) + (count_H * 2) + (min (count_G, count_Y) * 5)

# Everything below is the CLI walkthrough; only runs when this file is executed directly,
# so gui.py (and anything else) can import breed_slot/breed/score without it firing.
if __name__ == "__main__":
    demo()

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
    # Rust genetics sort individually. Think of each of the six genes as a slot.
    # We can calculate each slot outcome of a plant given its "slot neighbors." (the gene of a neighboring plant(s) at that slot)

    print("Slot winner:", breed_slot("X", ["G", "Y", "Y", "Y"]))

    # Step 4: Predicting a Plant
    # Same idea, run across all 6 slots of a real center plant and its neighbor plants.

    center_plant = "XYGWGG"
    neighbor_plants = ["GGGGGG", "GGGGGG"]
    print("Offspring:", breed(center_plant, neighbor_plants))
