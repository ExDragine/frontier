// 登录页面
const LoginPage = {
    template: `
        <div class="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold text-gray-800 mb-2">Frontier Dashboard</h1>
                    <p class="text-gray-500">请输入管理密码</p>
                </div>
                
                <form @submit.prevent="handleLogin" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
                        <input v-model="password"
                               type="password"
                               required
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
                               placeholder="输入管理密码">
                    </div>
                    
                    <button type="submit"
                            :disabled="loading"
                            :class="loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-indigo-700'"
                            class="w-full bg-primary text-white py-3 rounded-lg font-medium transition">
                        {{ loading ? '登录中...' : '登录' }}
                    </button>
                    
                    <div v-if="error" class="text-red-500 text-sm text-center">
                        {{ error }}
                    </div>
                </form>
            </div>
        </div>
    `,
    setup() {
        const { ref } = Vue;
        const router = Vue.inject('$router');
        const password = ref('');
        const loading = ref(false);
        const error = ref('');
        
        const handleLogin = async () => {
            loading.value = true;
            error.value = '';
            
            try {
                const response = await ApiClient.post('/auth/login', {
                    password: password.value
                });
                
                AuthUtils.setToken(response.token);
                showToast('登录成功', 'success');
                router.push('/');
            } catch (err) {
                error.value = err.message;
                showToast(err.message, 'error');
            } finally {
                loading.value = false;
            }
        };
        
        return { password, loading, error, handleLogin };
    }
};
