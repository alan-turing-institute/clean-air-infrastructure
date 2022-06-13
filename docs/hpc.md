# High performance computing
## Aquifer login
Aquifer contains a NVIDIA Titan GPU useful for prototyping and experimenting with models.
If you need to models for many days or weeks at a time, perhaps one of Warwick's scientific clusters would be more suitable.

### How to connect

If you have a user account, simply use ssh:

```
ssh USERNAME@aquifer.dcs.warwick.ac.uk
```

- Print GPUs detail

```bash
sudo lshw -C display
```

### I need help!

Ask one of our admins:

| Name        | Email |
| ----------- | ----------- |
| Sueda Ciftci      | Sueda.Ciftci@warwick.ac.uk       |
| Patrick O'Hara   | Patrick.H.O-Hara@warwick.ac.uk      |

Problems with the GPUs? Maybe DCS team can help. Contact unixhelp@dcs.warwick.ac.uk

## Using docker on aquifer

After cloning the repository to run docker on aquifer you will need sudo access (ask the aquifer admin).
Prefix any docker commands you run with the **sudo** keyword, e.g.

```
sudo docker pull python:3.9
```

For login to Azure container registry (London Air Quality Project) please find the instruction [here](docker.md)