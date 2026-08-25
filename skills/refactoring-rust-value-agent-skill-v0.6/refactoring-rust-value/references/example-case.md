# Example Case — Shared Scheduler State → Single-Owner Task

> This is illustrative. Replace with real project code and evidence.

**Priority:** Critical

## Why this case matters

The scheduler is on the request execution path. Its synchronization model affects correctness, latency, and maintainability across the runtime.

## Before — C/C++

```cpp
class Scheduler {
public:
    void enqueue(Job* job) {
        std::lock_guard<std::mutex> lock(mu_);
        queue_.push(job);
        cv_.notify_one();
    }

    void cancel(JobId id) {
        std::lock_guard<std::mutex> lock(mu_);
        cancelled_.insert(id);
    }

private:
    std::mutex mu_;
    std::condition_variable cv_;
    std::queue<Job*> queue_;
    std::unordered_set<JobId> cancelled_;
};
```

The correctness model depends on a shared-state invariant:

```text
Any mutation of queue_ or cancelled_ must occur while mu_ is held,
and Job* must remain valid while queued or processed.
```

## After — Rust

```rust
enum Command {
    Enqueue(Job),
    Cancel(JobId),
}

struct Scheduler {
    rx: mpsc::Receiver<Command>,
    queue: VecDeque<Job>,
    cancelled: HashSet<JobId>,
}

impl Scheduler {
    async fn run(mut self) {
        while let Some(cmd) = self.rx.recv().await {
            match cmd {
                Command::Enqueue(job) => self.queue.push_back(job),
                Command::Cancel(id) => { self.cancelled.insert(id); }
            }
        }
    }
}
```

## What changed semantically

This is not merely `std::mutex → Rust Mutex`. Mutation authority moved from many callers sharing internal state to one task owning scheduler state. Other components send commands instead of directly mutating scheduler internals.

## Value created

- synchronization reasoning is localized to one owner
- queue/cancellation state no longer requires a lock for each internal mutation
- data flow is explicit through commands
- queued jobs are moved as owned values rather than represented as unmanaged pointers
- state transitions become easier to test as command handling

## Why this value appeared

### General redesign

A single-owner/event-loop architecture is possible in C++ and provides much of the same structural simplification.

### Rust-driven design

Rust's ownership model makes “one component owns the mutable state; others transfer messages” a natural fit and makes broad shared mutation comparatively explicit/expensive to model.

### Rust guarantees

- `Job` movement through the channel makes ownership transfer explicit.
- Cross-thread transport is constrained by `Send` where applicable.
- The scheduler's mutable state is accessible through `&mut self` inside its owned task.
- Safe Rust prevents unmanaged raw-pointer dereference in this path.

## Counterfactual modern C++

Modern C++ can implement the same command/event-loop design and can use move-only messages and smart pointers. The architectural value remains. Rust changes the enforcement baseline: ownership transfer, aliasing restrictions, and thread-transfer traits are integrated into the language/type system rather than being mostly API/library discipline.

## Trade-offs

- channel scheduling and allocation may have runtime cost
- backpressure behavior must be designed explicitly
- task shutdown semantics still require careful handling
