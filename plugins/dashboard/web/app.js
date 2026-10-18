const { createApp } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;


const routes = [
    { path: '/login', component: LoginPage, meta: { public: true } },
    { path: '/', component: DashboardPage },
    { path: '/tasks', component: TasksPage },
    { path: '/messages', component: MessagesPage },
    { path: '/settings', component: SettingsPage },
];

const router = createRouter({
    history: createWebHashHistory('/dashboard/'),
    routes,
});


router.beforeEach((to, from, next) => {
    if (!to.meta.public && !AuthUtils.isLoggedIn()) {
        next('/login');
    } else if (to.path === '/login' && AuthUtils.isLoggedIn()) {
        next('/');
    } else {
        next();
    }
});


const App = {
    template: `
        <div v-if="!isLoginPage" class="flex flex-col md:flex-row h-screen overflow-hidden">
            <Sidebar />
            <div class="flex-1 min-w-0 min-h-0 flex flex-col overflow-hidden">
                <Header :botName="botName" :botConnected="botConnected" />
                <main class="flex-1 overflow-y-auto p-4 md:p-6 bg-gray-50">
                    <router-view></router-view>
                </main>
            </div>
        </div>
        <div v-else>
            <router-view></router-view>
        </div>
        <ToastContainer />
    `,
    setup() {
        const { ref, computed } = Vue;
        const route = router.currentRoute;
        const botName = ref('Frontier');
        const botConnected = ref(undefined);

        const isLoginPage = computed(() => route.value.path === '/login');


        const fetchBotInfo = async () => {
            if (AuthUtils.isLoggedIn()) {
                try {
                    const status = await ApiClient.get('/status/overview');
                    botName.value = status.bot_name;
                    botConnected.value = status.bot_connected;
                } catch (err) {

                }
            }
        };

        fetchBotInfo();

        return { isLoginPage, botName, botConnected, route };
    },
    provide() {
        return {
            $router: router,
            $route: router.currentRoute
        };
    }
};


const app = createApp(App);
app.component('Sidebar', SidebarComponent);
app.component('Header', HeaderComponent);
app.component('ToastContainer', ToastComponent);
app.component('Pagination', PaginationComponent);
app.use(router);
app.mount('#app');
