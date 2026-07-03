import { session } from "@web/session";
import { browser } from "../../core/browser/browser";
import { registry } from "../../core/registry";

const loadMenusUrl = `/web/webclient/load_menus`;

export const menuService = {
    dependencies: ["action"],
    async start(env) {
        let currentAppId;
        let menusData;

        const fetchMenus = async (reload) => {
            if (!reload && odoo.loadMenusPromise) {
                return odoo.loadMenusPromise;
            }
            const res = await browser.fetch(loadMenusUrl, { cache: "no-store" });
            if (!res.ok) {
                throw new Error("Error while fetching menus");
            }
            return res.json();
        };
        const storedMenus = browser.localStorage.getItem("webclient_menus");
        const storedMenusVersion = browser.localStorage.getItem("webclient_menus_version");

        if (storedMenus && storedMenusVersion === session.registry_hash) {
            fetchMenus().then((res) => {
                if (res) {
                    const fetchedMenus = JSON.stringify(res);
                    if (fetchedMenus !== storedMenus) {
                        try {
                            browser.localStorage.setItem("webclient_menus", fetchedMenus);
                        } catch (error) {
                            console.error("Error while storing menus in localStorage", error);
                        }
                        menusData = res;
                        env.bus.trigger("MENUS:APP-CHANGED");
                    }
                }
            });
            menusData = JSON.parse(storedMenus);
        } else {
            menusData = await fetchMenus();
            if (menusData) {
                try {
                    browser.localStorage.setItem("webclient_menus_version", session.registry_hash);
                    browser.localStorage.setItem("webclient_menus", JSON.stringify(menusData));
                } catch (error) {
                    console.error("Error while storing menus in localStorage", error);
                }
            }
        }

        function _getMenu(menuId) {
            return menusData[menuId];
        }
        function setCurrentMenu(menu) {
            // uuid: menu ids are uuid strings now, resolve any non-object id (number or string)
            menu = menu && typeof menu === "object" ? menu : _getMenu(menu);
            if (menu && menu.appID !== currentAppId) {
                currentAppId = menu.appID;
                browser.sessionStorage.setItem("menu_id", currentAppId);
                env.bus.trigger("MENUS:APP-CHANGED");
            }
        }

        return {
            getAll() {
                return Object.values(menusData);
            },
            getApps() {
                return this.getMenu("root").children.map((mid) => this.getMenu(mid));
            },
            getMenu: _getMenu,
            getCurrentApp() {
                if (!currentAppId) {
                    return;
                }
                return this.getMenu(currentAppId);
            },
            getMenuAsTree(menuID) {
                const menu = this.getMenu(menuID);
                if (!menu.childrenTree) {
                    menu.childrenTree = menu.children.map((mid) => this.getMenuAsTree(mid));
                }
                return menu;
            },
            async selectMenu(menu) {
                // uuid: resolve any non-object id (number or uuid string) to its menu
                menu = menu && typeof menu === "object" ? menu : this.getMenu(menu);
                if (!menu.actionID) {
                    return;
                }
                await env.services.action.doAction(menu.actionID, {
                    clearBreadcrumbs: true,
                    onActionReady: () => {
                        setCurrentMenu(menu);
                    },
                });
            },
            setCurrentMenu,
            async reload() {
                if (fetchMenus) {
                    menusData = await fetchMenus(true);
                    env.bus.trigger("MENUS:APP-CHANGED");
                }
            },
        };
    },
};

registry.category("services").add("menu", menuService);
