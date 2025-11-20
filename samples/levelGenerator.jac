import from byllm.lib { Model }
glob llm = Model(model_name="ollama/llama3");

obj Position {
    has x: int;
    has y: int;
}
obj Wall {
    has start_pos: Position;
    has end_pos: Position;
}

obj Map {
    has walls: list[Wall];
    has enemies: list[Position];
    has player_pos: Position;
}

obj Level {
    has name: str;
    has level_id: int;
    has difficulty: str;
    has width: int;
    has height: int;
    has num_wall: int;
    has num_enemies: int;
    has map: Map;
}

def visualize(level: Level) -> str {
    # Create an empty grid
    let grid = [];
    for y in range(level.height) {
        let row = [];
        for x in range(level.width) {
            row.append(".");
        }
        grid.append(row);
    }

    # Draw walls
    for w in level.map.walls {
        let x1 = w.start_pos.x;
        let y1 = w.start_pos.y;
        let x2 = w.end_pos.x;
        let y2 = w.end_pos.y;

        if x1 == x2 {
            # vertical
            let ystart = y1 if y1 < y2 else y2;
            let yend = y2 if y2 > y1 else y1;
            for y in range(ystart, yend + 1) {
                grid[y][x1] = "#";
            }
        }
        elif y1 == y2 {
            # horizontal
            let xstart = x1 if x1 < x2 else x2;
            let xend = x2 if x2 > x1 else x1;
            for x in range(xstart, xend + 1) {
                grid[y1][x] = "#";
            }
        }
    }

    # mark enemies
    for e in level.map.enemies {
        grid[e.y][e.x] = "E";
    }

    # mark player
    grid[level.map.player_pos.y][level.map.player_pos.x] = "P";

    # Convert to multiline string
    let out = "";
    for r in grid {
        out += "".join(r) + "\n";
    }
    return out;
}


with entry {
    let lvl = Level(
        name = "Forest Entrance",
        level_id = 1,
        difficulty = "Easy",
        width = 20,
        height = 10,
        num_wall = 2,
        num_enemies = 2,
        map = Map(
            walls = [
                Wall(
                    start_pos = Position(x = 2, y = 2),
                    end_pos = Position(x = 10, y = 2)
                ),
                Wall(
                    start_pos = Position(x = 5, y = 5),
                    end_pos = Position(x = 5, y = 8)
                )
            ],
            enemies = [
                Position(x = 15, y = 4),
                Position(x = 17, y = 7)
            ],
            player_pos = Position(x = 1, y = 1)
        )
    );

}


def get_next_level(prev_levels: list[Level]) -> Level by llm();


with entry {
    next_level = get_next_level(prev_levels=[lvl]);
    print("Previous Level:");
    print(visualize(lvl));
    print("Next Level:");
    print(visualize(next_level));
    print(next_level);

}