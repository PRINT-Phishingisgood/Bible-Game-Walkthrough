Here is an updated, polished version of your `README.md` that reflects all the massive upgrades, new mini-games, and Redis Cloud features you’ve built into the project!

You can copy and paste this directly into your repository:

---

# Bible Quest 🕹️

**Play the Stories. Conquer the Leaderboard.**

A top-down 2D arcade ecosystem built in Python/Pygame. Players step into a retro arcade hall, select their hero, and walk up to distinct cabinets to play custom, procedurally drawn minigames based on classic biblical narratives.

The entire arcade is backed by a live **Redis Cloud** database for global leaderboards, persistent player wallets, and live remote game balancing.

## 🚀 How to Run

Because the game now connects to the cloud, you will need to install the Redis python library alongside Pygame.

```bash
pip install pygame redis
python main.py

```

## 📂 Project Structure

```text
bible_game/
├── main.py                # The Arcade World — walkable hub & Redis engine
├── character_select.py    # Hero selection screen (Shepherd or Mary)
├── sheep_maze.py          # Game 1: The Lost Sheep (Luke 15:3–7)
├── fish_coin.py           # Game 2: Deep Sea Hook (Matthew 17:27)
├── david_sling.py         # Game 3: Sling Artillery (1 Samuel 17)
├── feed_crowd.py          # Game 4: Catch & Multiply (Matthew 14:20)
├── babel_tower.py         # Game 5: Tower of Babel (Genesis 11)
└── README.md              # This file

```

## 🎮 Controls

| Key | Action |
| --- | --- |
| **WASD / Arrows** | Move your character around the arcade / play minigames |
| **ENTER** | Interact with an arcade cabinet / confirm selection |
| **ESC** | Open Settings Menu / Return to the Arcade Hall |

## 🌟 Features

* **Cloud Leaderboards:** Instant $O(\log N)$ global rank updates submitted directly to Redis Sorted Sets.
* **Persistent Profiles:** Earn "Fish Coins" in minigames that save to your hero's permanent cloud wallet.
* **Live Game Tuning:** Minigame physics (like Goliath's walk speed or stone gravity) are pulled from a live Redis Hash (`game:config`), allowing the developer to re-balance the game without modifying local code.
* **Zero External Assets:** Every sprite, bush, brick, and giant is calculated mathematically using layered geometric primitives (`pygame.draw`).

## 🕹️ The Arcade Cabinets

### 🐑 The Lost Sheep

Find all 5 sheep hidden in a bush-filled maze. The maze is covered in fog — you can only see a small circle around your shepherd. *Based on Luke 15:4.*

### 🐋 Deep Sea Arcade Hook

Cast your line into the depths, dodge obstacles, and surface safely to discover a piece of money inside the fish. Earn Fish Coins for your cloud wallet based on your speed! *Based on Matthew 17:27.*

### 🪨 Sling Artillery (David & Goliath)

A physics-based projectile game with sub-stepped precision hitboxes. Calculate your trajectory and strike Goliath before he crosses the screen. *Based on 1 Samuel 17.*

### 🍞 Catch and Multiply (Feeding the 5,000)

An accelerating inventory-catching game. Move quickly to catch the falling loaves and fishes to feed the growing crowd. *Based on Matthew 14:20.*

### 🧱 Tower of Babel

A frantic platformer where multi-language confusion periodically reverses your controls. *Based on Genesis 11.*

## 🛠️ Technical Notes

* **Maze algorithm:** Recursive Backtracker (Depth-First Search) generating perfect labyrinths.
* **Physics Integration:** Semi-implicit Euler method utilizing discrete sub-stepping ($\Delta t_{\text{sub}}$) to prevent high-velocity projectiles from tunneling through hitboxes.
* **Network Stability:** Strict socket timeouts insulate the `pygame` loop from network latency or dropped packets.
