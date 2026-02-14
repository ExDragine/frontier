// 设置编辑页面
const SettingsPage = {
    template: `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-gray-800">系统设置</h1>
                <span v-if="saving" class="text-sm text-gray-500">保存中...</span>
            </div>

            <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>

            <template v-else>
                <div class="bg-white rounded-lg shadow">
                    <div class="border-b flex overflow-x-auto">
                        <button v-for="tab in tabs" :key="tab.key"
                                @click="activeTab = tab.key"
                                :class="activeTab === tab.key
                                    ? 'border-b-2 border-primary text-primary bg-indigo-50'
                                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'"
                                class="px-5 py-3 text-sm font-medium whitespace-nowrap transition">
                            {{ tab.label }}
                        </button>
                    </div>

                    <div class="p-6">
                        <div v-if="configData[activeTab]" class="space-y-5">
                            <div v-for="(value, key) in configData[activeTab]" :key="key" class="flex flex-col gap-1.5">
                                <label class="text-sm font-medium text-gray-700">{{ key }}</label>

                                <template v-if="typeof value === 'boolean'">
                                    <button @click="configData[activeTab][key] = !configData[activeTab][key]"
                                            :class="configData[activeTab][key] ? 'bg-green-500' : 'bg-gray-300'"
                                            class="relative w-12 h-6 rounded-full transition">
                                        <span :class="configData[activeTab][key] ? 'translate-x-6' : 'translate-x-0.5'"
                                              class="absolute top-0.5 left-0 w-5 h-5 bg-white rounded-full shadow transition-transform"></span>
                                    </button>
                                </template>

                                <template v-else-if="Array.isArray(value)">
                                    <div class="flex flex-wrap gap-2 items-center">
                                        <span v-for="(item, idx) in value" :key="idx"
                                              class="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                                            {{ item }}
                                            <button @click="removeArrayItem(activeTab, key, idx)"
                                                    class="text-blue-400 hover:text-blue-600 ml-1">x</button>
                                        </span>
                                        <input :placeholder="'添加...'"
                                               @keyup.enter="addArrayItem(activeTab, key, $event)"
                                               class="border rounded px-3 py-1 text-sm w-32">
                                    </div>
                                </template>

                                <template v-else-if="isSensitive(activeTab, key)">
                                    <div class="flex gap-2">
                                        <input :type="showSecrets[activeTab + '.' + key] ? 'text' : 'password'"
                                               v-model="configData[activeTab][key]"
                                               class="flex-1 border rounded px-3 py-2 text-sm font-mono">
                                        <button @click="toggleSecret(activeTab, key)"
                                                class="px-3 py-2 border rounded text-sm text-gray-600 hover:bg-gray-50">
                                            {{ showSecrets[activeTab + '.' + key] ? '隐藏' : '显示' }}
                                        </button>
                                    </div>
                                </template>

                                <template v-else-if="typeof value === 'number'">
                                    <input type="number" v-model.number="configData[activeTab][key]"
                                           class="border rounded px-3 py-2 text-sm w-48">
                                </template>

                                <template v-else>
                                    <input type="text" v-model="configData[activeTab][key]"
                                           class="border rounded px-3 py-2 text-sm">
                                </template>
                            </div>

                            <div v-if="Object.keys(configData[activeTab] || {}).length === 0"
                                 class="text-center text-gray-500 py-8">
                                此配置段暂无配置项
                            </div>
                        </div>

                        <div class="mt-6 pt-4 border-t flex gap-3">
                            <button @click="saveSection"
                                    :disabled="saving"
                                    class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50">
                                保存此配置段
                            </button>
                            <button @click="fetchConfig"
                                    class="px-6 py-2 border rounded-lg text-gray-700 hover:bg-gray-50">
                                重新加载
                            </button>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    `,
    setup() {
        const { ref, reactive, onMounted } = Vue;
        const loading = ref(false);
        const saving = ref(false);
        const activeTab = ref('information');
        const configData = reactive({});
        const showSecrets = reactive({});

        const tabs = [
            { key: 'information', label: '基本信息' },
            { key: 'endpoint', label: '接口配置' },
            { key: 'key', label: '密钥管理' },
            { key: 'function', label: '功能开关' },
            { key: 'message', label: '消息推送' },
            { key: 'database', label: '数据库' },
            { key: 'debug', label: '调试' },
            { key: 'schedule', label: '计划任务' },
            { key: 'memory', label: '记忆系统' },
            { key: 'dashboard', label: 'Dashboard' },
        ];

        const sensitiveFields = {
            key: new Set(['openai_api_key', 'nasa_api_key', 'github_pat']),
            dashboard: new Set(['jwt_secret', 'password']),
        };

        const isSensitive = (section, key) => {
            return sensitiveFields[section] && sensitiveFields[section].has(key);
        };

        const toggleSecret = (section, key) => {
            const k = section + '.' + key;
            showSecrets[k] = !showSecrets[k];
        };

        const fetchConfig = async () => {
            loading.value = true;
            try {
                const data = await ApiClient.get('/settings/');
                // 清空并重新填充 reactive 对象
                Object.keys(configData).forEach(k => delete configData[k]);
                Object.assign(configData, data.config);
            } catch (err) {
                showToast('加载配置失败: ' + err.message, 'error');
            } finally {
                loading.value = false;
            }
        };

        const saveSection = async () => {
            saving.value = true;
            try {
                const sectionData = configData[activeTab.value];
                if (!sectionData) return;

                await ApiClient.put(`/settings/${activeTab.value}`, { config: sectionData });
                showToast('配置已保存并生效', 'success');
            } catch (err) {
                showToast('保存失败: ' + err.message, 'error');
            } finally {
                saving.value = false;
            }
        };

        const removeArrayItem = (section, key, idx) => {
            configData[section][key].splice(idx, 1);
        };

        const addArrayItem = (section, key, event) => {
            const val = event.target.value.trim();
            if (!val) return;
            // 尝试转为数字
            const num = Number(val);
            configData[section][key].push(isNaN(num) ? val : num);
            event.target.value = '';
        };

        onMounted(fetchConfig);

        return {
            loading, saving, activeTab, configData, showSecrets, tabs,
            isSensitive, toggleSecret, fetchConfig, saveSection,
            removeArrayItem, addArrayItem
        };
    }
};
