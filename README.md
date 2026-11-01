## rustbreeder.py

Clone of rustbreeder.com. Prior knowledge of the video game Rust and its in-game plant breeding mechanics is recommended. In short: the program takes a user's held plant genes and spits back the best plant you can currently breed, and instructions on where to plant your plants. 

<img width="419" height="40" alt="Screenshot 2026-10-31 at 10 24 02 PM" src="https://github.com/user-attachments/assets/be71c122-5be1-43b5-942f-47b60ecbf0a4" />
<img width="271" height="190" alt="Screenshot 2026-10-31 at 10 24 14 PM" src="https://github.com/user-attachments/assets/3985b8d1-8e75-4ed1-88da-b876a891b586" />
<img width="274" height="69" alt="Screenshot 2026-10-31 at 10 24 30 PM" src="https://github.com/user-attachments/assets/9a8187b3-f105-41a3-981d-dbff5f92d21f" />
<img width="1290" height="247" alt="Screenshot 2026-10-31 at 10 24 39 PM" src="https://github.com/user-attachments/assets/bef97f38-f579-4053-bc11-2994b9b868e6" />

Features: 

Input box for a user's held plants.
Each plant has 6 genes, and each gene can be one of five traits: Growth, Yield, Hardiness, Water, or Nothing.
We're aiming to maximize growth and yield genes. The "god clone" is GGGYYY. (three growth, three yield).
Python program assigns a value to each gene and ranks the user's held plants.
Runs a program to solve for the best possible plant outcome. (following Rust's own crossbreeding rules: read more on the actual rustbreeder website: https://rustbreeder.com/guide/)

Clean UI displaying where you should plant your plants, and the resulting plants once they've matured.

Live deployment at: https://rustbreeder.vercel.app/
Run locally:
git clone https://github.com/winterrmelonn/rustbreeder.py.git
cd rustbreeder.py
python3 gui.py (requires Tkinter and Python v2.8 or newer)
