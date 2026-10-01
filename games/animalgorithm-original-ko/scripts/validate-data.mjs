import fs from "node:fs";

const animals = JSON.parse(
  fs.readFileSync(new URL("../data/animals.plix-ko.json", import.meta.url), "utf8")
);
const categories = JSON.parse(
  fs.readFileSync(new URL("../data/category_pairs.plix-ko.json", import.meta.url), "utf8")
);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(animals.namedAnimalCards === 46, "namedAnimalCards must be 46");
assert(animals.blankAnimalCards === 10, "blankAnimalCards must be 10");
assert(animals.animals.length === 46, "animals array must contain 46 records");

const ids = new Set(animals.animals.map((a) => a.id));
assert(ids.size === 46, "animal IDs must be unique");

const positions = new Set(
  animals.animals.map((a) => `${a.sourcePage}:${a.sourceSlot}`)
);
assert(positions.size === 46, "source page/slot positions must be unique");

assert(categories.categoryIdeaCards === 8, "categoryIdeaCards must be 8");
assert(categories.pairs.length === 8, "category pairs array must contain 8 records");

console.log("OK: PLIX original localization data integrity checks passed.");
