// 侧边栏导航组件
const SidebarComponent = {
    template: `
        <div class="w-full md:w-64 shrink-0 bg-white shadow-lg md:h-screen flex flex-col">
            <div class="hidden md:block p-6 border-b">
                <h1 class="text-2xl font-bold text-primary">Frontier</h1>
                <p class="text-sm text-gray-500 mt-1">Dashboard</p>
            </div>
            <nav class="flex-1 grid grid-cols-4 md:block p-2 md:p-4 md:space-y-2">
                <router-link v-for="item in navItems" :key="item.path"
                             :to="item.path"
                             class="flex flex-col md:flex-row items-center gap-1 md:gap-3 px-1 md:px-4 py-3 text-xs md:text-base rounded-lg transition-colors"
                             :class="isActive(item.path) ? 'bg-primary text-white' : 'text-gray-700 hover:bg-gray-100'">
                    <span>{{ item.icon }}</span>
                    <span>{{ item.label }}</span>
                </router-link>
            </nav>
        </div>
    `,
    setup() {
        const route = Vue.inject('$route');
        
        const navItems = [
            { path: '/', icon: '📊', label: '总览' },
            { path: '/tasks', icon: '⏰', label: '定时任务' },
            { path: '/messages', icon: '💬', label: '对话历史' },
            { path: '/settings', icon: '⚙️', label: '设置' },
        ];
        
        const isActive = (path) => {
            return route.value.path === path || 
                   (path !== '/' && route.value.path.startsWith(path));
        };
        
        return { navItems, isActive, route };
    }
};
