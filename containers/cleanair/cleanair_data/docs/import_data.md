## Input data to data base

Use `urbanair_db` cli to insert data into data bases. E.g.

```
urbanair_db inputs <source> fill --ndays <number-of-days> --upto <time(eg.2023-06-21)> 
```

PS: Excessive data input at once can potentially overwhelm the server, resulting in high server load and increased database activity, which, in turn, may cause delays in establishing connections, leading to timeouts.
