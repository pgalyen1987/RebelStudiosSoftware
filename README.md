# Rebel Studios Software

Portfolio and blog site for [Rebel Studios Software](https://rebelstudiossoftware.com) — custom Android apps, SaaS platforms, and engineering research.

## License (split)

This repository uses a **split license**:

| What | License | File |
|------|---------|------|
| Site source code (HTML/CSS/JS, scripts, SEO files) | [MIT](LICENSE) | `LICENSE` |
| Blog articles, research paper, marketing prose | All rights reserved | [CONTENT-LICENSE](CONTENT-LICENSE) |

You may fork and reuse the **site template** under MIT. The **written content** inside blog and research pages is not open source.

## Local development

Static site — open `index.html` in a browser or serve the directory:

```bash
python3 -m http.server 8080
```

## Blog maintenance

After adding a blog post, regenerate the sitemap and RSS feed:

```bash
python3 generate_feeds.py
```

## Related open-source projects

- [Vigilo](https://github.com/pgalyen1987/Vigilo) — open-source v0.1.0 research prototype for on-device network anomaly detection (Mamba-2 forecaster, Zeek conn.log, Apache 2.0)
