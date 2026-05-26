from process import Process

isRunning = True

# make input later, use pre defined processes for now
x = Process(
    pid= 2,
    arrival_time=3,
    burst_time=5,
    priority=1
)

y = Process(
    pid= 1,
    arrival_time=0,
    burst_time=2,
    priority=0
)

z = Process(
    pid=3,
    arrival_time=2,
    burst_time=4,
    priority=2
)

processes: list[Process]  = [x, y, z]

def main():
    """
    for each loop, evaluate processes based on algorithm
    """
    

if __name__ == "__main__":
    while (isRunning):
        main()
