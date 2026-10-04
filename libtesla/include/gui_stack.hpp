#pragma once

#include <list>
#include <memory>
#include <stack>
#include <vector>

namespace tsl::impl {

// A callback can pop its own GUI. Keep it and its elements alive until dispatch
// returns, including the std::function which is currently executing.
template<class Gui>
class GuiStack {
public:
    using GuiPtr = std::unique_ptr<Gui>;

    class DispatchScope {
    public:
        explicit DispatchScope(GuiStack& stack) : m_stack(stack) { ++m_stack.m_dispatchDepth; }
        DispatchScope(const DispatchScope&) = delete;
        DispatchScope& operator=(const DispatchScope&) = delete;
        ~DispatchScope() {
            if (--m_stack.m_dispatchDepth == 0) m_stack.m_retired.clear();
        }
    private:
        GuiStack& m_stack;
    };

    DispatchScope dispatch() { return DispatchScope(*this); }
    bool empty() const { return m_stack.empty(); }
    std::size_t size() const { return m_stack.size(); }
    GuiPtr& top() { return m_stack.top(); }
    const GuiPtr& top() const { return m_stack.top(); }
    void push(GuiPtr gui) { m_stack.push(std::move(gui)); }
    void pop() {
        if (m_dispatchDepth) m_retired.push_back(std::move(m_stack.top()));
        m_stack.pop();
    }

private:
    std::stack<GuiPtr, std::list<GuiPtr>> m_stack;
    std::vector<GuiPtr> m_retired;
    unsigned m_dispatchDepth = 0;
};
}
