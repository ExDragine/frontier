// 任务列表页面
const TasksPage = {
    template: `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-gray-800">定时任务管理</h1>
                <button @click="fetchTasks" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-indigo-600">
                    刷新
                </button>
            </div>
            
            <div class="bg-white rounded-lg shadow p-4 flex gap-4">
                <div>
                    <label class="text-sm text-gray-600 mb-1 block">状态筛选</label>
                    <select v-model="filter" @change="fetchTasks" class="border rounded px-3 py-2">
                        <option value="all">全部</option>
                        <option value="enabled">已启用</option>
                        <option value="disabled">已禁用</option>
                    </select>
                </div>
                <div class="flex-1">
                    <label class="text-sm text-gray-600 mb-1 block">搜索</label>
                    <input v-model="keyword" @input="debouncedFetch" type="text"
                           placeholder="搜索任务名称或 ID..."
                           class="w-full border rounded px-3 py-2">
                </div>
            </div>
            
            <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
            
            <div v-else-if="tasks.length === 0" class="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                暂无任务
            </div>
            
            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div v-for="task in tasks" :key="task.job_id"
                     class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-800">{{ task.name }}</h3>
                            <p class="text-sm text-gray-500 font-mono">{{ task.job_id }}</p>
                        </div>
                        <button @click="toggleTask(task)"
                                :class="task.enabled ? 'bg-green-500' : 'bg-gray-400'"
                                class="px-3 py-1 text-white text-sm rounded hover:opacity-80">
                            {{ task.enabled ? '已启用' : '已禁用' }}
                        </button>
                    </div>
                    
                    <p v-if="task.description" class="text-sm text-gray-600 mb-3">{{ task.description }}</p>
                    
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-600">触发类型</span>
                            <span class="font-medium">{{ triggerLabel(task) }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">执行统计</span>
                            <span class="font-medium">成功 {{ task.success_runs }} / 失败 {{ task.failed_runs }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">推送群组</span>
                            <span class="font-medium">{{ task.groups.length }} 个</span>
                        </div>
                    </div>
                    
                    <div class="mt-4 pt-4 border-t flex gap-2">
                        <button @click="viewDetail(task.job_id)"
                                class="flex-1 px-3 py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100">
                            查看详情
                        </button>
                        <button @click="viewHistory(task.job_id)"
                                class="flex-1 px-3 py-2 bg-gray-50 text-gray-600 rounded hover:bg-gray-100">
                            执行历史
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div v-if="detailTask" @click.self="detailTask = null"
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-xl font-bold">{{ detailTask.name }}</h2>
                    <button @click="detailTask = null" class="text-gray-500 hover:text-gray-700">✕</button>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="text-sm font-medium text-gray-700">触发配置</label>
                        <pre class="mt-1 p-3 bg-gray-50 rounded text-sm">{{ JSON.stringify(detailTask.trigger_args, null, 2) }}</pre>
                    </div>
                    
                    <div>
                        <label class="text-sm font-medium text-gray-700 block mb-2">推送群组</label>
                        <div class="flex flex-wrap gap-2">
                            <span v-for="groupId in detailTask.groups" :key="groupId"
                                  class="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">
                                {{ groupId }}
                            </span>
                            <span v-if="detailTask.groups.length === 0" class="text-gray-500 text-sm">未配置</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div v-if="historyTask" @click.self="historyTask = null"
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
                <div class="sticky top-0 bg-white border-b p-6 flex justify-between items-center">
                    <h2 class="text-xl font-bold">执行历史</h2>
                    <button @click="historyTask = null" class="text-gray-500 hover:text-gray-700">✕</button>
                </div>
                
                <div v-if="history.length === 0" class="p-12 text-center text-gray-500">暂无执行记录</div>
                
                <table v-else class="w-full">
                    <thead class="bg-gray-50 border-b">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">耗时</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">消息数</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y">
                        <tr v-for="h in history" :key="h.id" class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-gray-900">{{ formatTime(h.execution_time) }}</td>
                            <td class="px-6 py-4">
                                <span :class="statusClass(h.status)" class="px-2 py-1 rounded text-xs font-medium">
                                    {{ h.status }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">{{ h.duration_ms ? h.duration_ms + 'ms' : '-' }}</td>
                            <td class="px-6 py-4 text-sm text-gray-900">{{ h.messages_sent || 0 }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,
    setup() {
        const { ref, onMounted } = Vue;
        const tasks = ref([]);
        const loading = ref(false);
        const filter = ref('all');
        const keyword = ref('');
        const detailTask = ref(null);
        const historyTask = ref(null);
        const history = ref([]);
        
        const fetchTasks = async () => {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                if (filter.value !== 'all') {
                    params.append('enabled', filter.value === 'enabled');
                }
                if (keyword.value) {
                    params.append('keyword', keyword.value);
                }

                const data = await ApiClient.get('/tasks/?' + params);
                tasks.value = data.tasks;
            } catch (err) {
                showToast('加载失败: ' + err.message, 'error');
            } finally {
                loading.value = false;
            }
        };

        let debounceTimer = null;
        const debouncedFetch = () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(fetchTasks, 300);
        };

        const toggleTask = async (task) => {
            try {
                const endpoint = task.enabled ? 'disable' : 'enable';
                await ApiClient.put(`/tasks/${task.job_id}/${endpoint}`, {});
                showToast(task.enabled ? '已禁用' : '已启用', 'success');
                await fetchTasks();
            } catch (err) {
                showToast('操作失败: ' + err.message, 'error');
            }
        };
        
        const viewDetail = async (jobId) => {
            try {
                const data = await ApiClient.get(`/tasks/${jobId}`);
                detailTask.value = data;
            } catch (err) {
                showToast('加载详情失败: ' + err.message, 'error');
            }
        };
        
        const viewHistory = async (jobId) => {
            try {
                const data = await ApiClient.get(`/tasks/${jobId}/history`);
                history.value = data.history;
                historyTask.value = jobId;
            } catch (err) {
                showToast('加载历史失败: ' + err.message, 'error');
            }
        };
        
        const triggerLabel = (task) => {
            if (task.trigger_type === 'cron') {
                const args = task.trigger_args;
                if (args.hour !== undefined && args.minute !== undefined) {
                    return `每天 ${args.hour}:${args.minute}`;
                }
                return 'Cron';
            } else if (task.trigger_type === 'interval') {
                const args = task.trigger_args;
                if (args.minutes) return `每 ${args.minutes} 分钟`;
                if (args.hours) return `每 ${args.hours} 小时`;
                return '定时';
            }
            return task.trigger_type;
        };
        
        const formatTime = (ms) => {
            if (!ms) return '-';
            const date = new Date(ms);
            return date.toLocaleString('zh-CN');
        };
        
        const statusClass = (status) => {
            if (status === 'success') return 'bg-green-100 text-green-800';
            if (status === 'failed') return 'bg-red-100 text-red-800';
            return 'bg-gray-100 text-gray-800';
        };
        
        onMounted(fetchTasks);
        
        return {
            tasks, loading, filter, keyword, detailTask, historyTask, history,
            fetchTasks, debouncedFetch, toggleTask, viewDetail, viewHistory, triggerLabel, formatTime, statusClass
        };
    }
};
