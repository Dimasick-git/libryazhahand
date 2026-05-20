/*
 * RyazhaHand example overlay -- минимальный демо-оверлей,
 * нужен чтобы CI (verify_build.yml) собирал библиотеку
 * end-to-end. Реальные оверлеи (Ryazhahand-Overlay, RCU и т.д.)
 * подключают libryazhahand как submodule и пишут собственный main.
 *
 * Автор: Dimasick-git
 * Лицензия: GPL-2.0 (см. ../../LICENSE)
 */

// TESLA_INIT_IMPL разворачивает в этой TU init-блок tesla.hpp
// (отдельный от libtesla/source/tesla.cpp). Должен стоять
// строго в одной TU оверлея.
#define TESLA_INIT_IMPL
#include <tesla.hpp>

namespace {

class ExampleGui : public tsl::Gui {
public:
    tsl::elm::Element* createUI() override {
        auto* frame = new tsl::elm::OverlayFrame("RyazhaHand Example",
                                                 APP_VERSION);
        auto* list = new tsl::elm::List();

        list->addItem(new tsl::elm::CategoryHeader("Демо"));
        list->addItem(new tsl::elm::ListItem("Привет, RyazhaHand"));
        list->addItem(new tsl::elm::ListItem("Это референсный оверлей"));

        frame->setContent(list);
        return frame;
    }
};

class ExampleOverlay : public tsl::Overlay {
public:
    void initServices() override {}
    void exitServices() override {}

    std::unique_ptr<tsl::Gui> loadInitialGui() override {
        return initially<ExampleGui>();
    }
};

} // namespace

int main(int argc, char** argv) {
    return tsl::loop<ExampleOverlay>(argc, argv);
}
