# Pynarist Benchmarks

Calculates the time cost of serializing and deserializing a `Person` structure with fields `name`, `age`, `fav_color.name` and `fav_color.hex_code`.

You can find the benchmark source code in `bench.py`.
By running the bench, you may get results like this:

| Tool | Serialize Time | Deserialize Time | Size |
|------|-----------|-------------|------|
| Pynarist | **65.3 µs** | **25.6 µs** | **18** |
| Pickle | 81.7 µs | 18.5 µs | 137 |
| Binpi | 92.4 µs | 52.9 µs | 17 |

Overall, Pynarist has a very small size and have a good performance, while pickle and binpi have problems about result sizes and performances.