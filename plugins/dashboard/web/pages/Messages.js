// 消息历史页面
const MessagesPage = {
    template: `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-gray-800">对话历史</h1>
                <button @click="fetchMessages" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-indigo-600">
                    刷新
                </button>
            </div>

            <div class="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4">
                <div>
                    <label class="text-sm text-gray-600 mb-1 block">群组</label>
                    <select v-model="selectedGroup" @change="onFilterChange" class="border rounded px-3 py-2 min-w-[160px]">
                        <option :value="null">全部群组</option>
                        <option v-for="g in groups" :key="g.group_id" :value="g.group_id">
                            {{ g.group_id }} ({{ g.message_count }})
                        </option>
                    </select>
                </div>
                <div>
                    <label class="text-sm text-gray-600 mb-1 block">角色</label>
                    <select v-model="selectedRole" @change="onFilterChange" class="border rounded px-3 py-2">
                        <option value="">全部</option>
                        <option value="user">用户</option>
                        <option value="assistant">助手</option>
                    </select>
                </div>
                <div class="flex-1 min-w-[200px]">
                    <label class="text-sm text-gray-600 mb-1 block">搜索内容</label>
                    <input v-model="searchText" @keyup.enter="onFilterChange" type="text"
                           placeholder="输入关键词后回车搜索..."
                           class="w-full border rounded px-3 py-2">
                </div>
                <div class="flex items-end">
                    <button @click="onFilterChange" class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                        搜索
                    </button>
                </div>
            </div>

            <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>

            <div v-else-if="messages.length === 0" class="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                暂无消息记录
            </div>

            <div v-else class="bg-white rounded-lg shadow overflow-hidden">
                <div class="divide-y max-h-[60vh] overflow-y-auto">
                    <div v-for="msg in messages" :key="msg.time"
                         class="px-6 py-4 hover:bg-gray-50 transition"
                         :class="msg.role === 'assistant' ? 'bg-blue-50/30' : ''">
                        <div class="flex items-center gap-3 mb-2">
                            <span :class="msg.role === 'assistant' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
                                  class="px-2 py-0.5 rounded text-xs font-medium">
                                {{ msg.role === 'assistant' ? '助手' : '用户' }}
                            </span>
                            <span class="text-sm text-gray-600">{{ msg.user_name || msg.user_id }}</span>
                            <span v-if="msg.group_id" class="text-xs text-gray-400">群 {{ msg.group_id }}</span>
                            <span class="text-xs text-gray-400 ml-auto">{{ formatTime(msg.time) }}</span>
                        </div>
                        <div class="text-sm text-gray-800 whitespace-pre-wrap break-words"
                             style="max-height: 200px; overflow-y: auto;">{{ msg.content }}</div>
                    </div>
                </div>

                <Pagination v-if="totalPages > 1"
                    :currentPage="page"
                    :totalPages="totalPages"
                    :total="total"
                    @change="onPageChange" />
            </div>
        </div>
    `,
    setup() {
        const { ref, onMounted } = Vue;
        const messages = ref([]);
        const groups = ref([]);
        const loading = ref(false);
        const page = ref(1);
        const total = ref(0);
        const totalPages = ref(1);
        const selectedGroup = ref(null);
        const selectedRole = ref('');
        const searchText = ref('');

        const fetchGroups = async () => {
            try {
                const data = await ApiClient.get('/messages/groups');
                groups.value = data.groups;
            } catch (err) {
                // 忽略
            }
        };

        const fetchMessages = async () => {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                params.append('page', page.value);
                params.append('page_size', '50');
                if (selectedGroup.value !== null) params.append('group_id', selectedGroup.value);
                if (selectedRole.value) params.append('role', selectedRole.value);
                if (searchText.value) params.append('search', searchText.value);

                const data = await ApiClient.get('/messages/?' + params);
                messages.value = data.messages;
                total.value = data.total;
                totalPages.value = data.total_pages;
            } catch (err) {
                showToast('加载消息失败: ' + err.message, 'error');
            } finally {
                loading.value = false;
            }
        };

        const onFilterChange = () => {
            page.value = 1;
            fetchMessages();
        };

        const onPageChange = (newPage) => {
            page.value = newPage;
            fetchMessages();
        };

        const formatTime = (ms) => {
            if (!ms) return '-';
            const date = new Date(ms);
            return date.toLocaleString('zh-CN');
        };

        onMounted(() => {
            fetchGroups();
            fetchMessages();
        });

        return {
            messages, groups, loading, page, total, totalPages,
            selectedGroup, selectedRole, searchText,
            fetchMessages, onFilterChange, onPageChange, formatTime
        };
    }
};
