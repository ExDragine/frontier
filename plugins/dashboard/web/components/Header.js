// 顶部栏组件
const HeaderComponent = {
    props: ['botName', 'botConnected'],
    template: `
        <div class="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <h2 class="text-xl font-semibold text-gray-800">{{ botName || '加载中...' }}</h2>
                <span v-if="botConnected !== undefined"
                      :class="botConnected ? 'bg-green-500' : 'bg-red-500'"
                      class="w-2 h-2 rounded-full"></span>
                <span v-if="botConnected !== undefined" class="text-sm text-gray-500">
                    {{ botConnected ? '已连接' : '未连接' }}
                </span>
            </div>
            <button @click="handleLogout"
                    class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                登出
            </button>
        </div>
    `,
    setup() {
        const handleLogout = () => {
            if (confirm('确定要登出吗？')) {
                AuthUtils.logout();
            }
        };
        
        return { handleLogout };
    }
};
