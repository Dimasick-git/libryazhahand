#include "../libtesla/include/gui_stack.hpp"
#include <cassert>
#include <functional>

struct Gui {
    static inline unsigned alive = 0;
    std::function<void()> click;
    Gui() { ++alive; }
    ~Gui() { --alive; }
};

int main() {
    tsl::impl::GuiStack<Gui> stack;
    stack.push(std::make_unique<Gui>());
    stack.push(std::make_unique<Gui>());
    Gui* menu = stack.top().get();
    menu->click = [&] {
        stack.pop();
        stack.pop();
        assert(stack.empty());
        assert(Gui::alive == 2); // Neither the callback nor its parent is deleted.
        stack.push(std::make_unique<Gui>());
        assert(stack.top().get() != menu); // No allocator-address reuse/ABA.
    };
    {
        auto outer = stack.dispatch();
        {
            auto inner = stack.dispatch();
            menu->click();
        }
        assert(Gui::alive == 3); // A nested return must not retire outer callbacks.
    }
    assert(Gui::alive == 1);
    {
        auto scope = stack.dispatch();
        stack.pop();
        assert(stack.empty() && Gui::alive == 1);
    }
    assert(Gui::alive == 0); // Closing the overlay also retires safely.
    stack.push(std::make_unique<Gui>());
    stack.pop();
    assert(Gui::alive == 0); // Outside dispatch destruction remains immediate.
}
