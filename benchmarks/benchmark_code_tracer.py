import time
from core.digital.code_tracer import code_tracer

def workload():
    val = 0

    for i in range(1000):
        val += 1

# without tracer
baseline_times = []
for _ in range(5):
    start = time.perf_counter()
    workload()
    end = time.perf_counter()
    baseline_times.append(end - start)

baseline = min(baseline_times)

# with tracer
traced_times = []
for _ in range(5):
    code_tracer.start_trace("__main__")
    start = time.perf_counter()
    workload()
    end = time.perf_counter()
    code_tracer.stop_trace()
    traced_times.append(end - start)

traced = min(traced_times)


# Results
overhead = ((traced - baseline) / baseline) * 100

print(f"Baseline:  {baseline * 1000:.2f} ms")
print(f"Traced:    {traced * 1000:.2f} ms")
print(f"Overhead:  {overhead:.2f}%")