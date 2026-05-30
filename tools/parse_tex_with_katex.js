const katex = require("katex");

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});

process.stdin.on("end", () => {
  const formulas = JSON.parse(input || "[]");
  const errors = [];
  for (const item of formulas) {
    try {
      katex.renderToString(item.tex, {
        displayMode: Boolean(item.display),
        throwOnError: true,
        strict: "ignore",
      });
    } catch (error) {
      errors.push({
        path: item.path,
        place: item.place,
        tex: item.tex,
        message: error && error.message ? error.message : String(error),
      });
    }
  }
  process.stdout.write(JSON.stringify(errors));
});
