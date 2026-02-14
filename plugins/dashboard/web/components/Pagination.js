// 分页组件
const PaginationComponent = {
    props: {
        currentPage: { type: Number, required: true },
        totalPages: { type: Number, required: true },
        total: { type: Number, required: true }
    },
    emits: ['change'],
    template: `
        <div class="flex items-center justify-between px-4 py-3 bg-white border-t">
            <div class="text-sm text-gray-700">
                共 <span class="font-medium">{{ total }}</span> 条记录
            </div>
            <div class="flex items-center gap-2">
                <button @click="$emit('change', currentPage - 1)"
                        :disabled="currentPage <= 1"
                        :class="currentPage <= 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'"
                        class="px-3 py-1 rounded border">
                    上一页
                </button>
                <span class="text-sm text-gray-700">
                    第 {{ currentPage }} / {{ totalPages }} 页
                </span>
                <button @click="$emit('change', currentPage + 1)"
                        :disabled="currentPage >= totalPages"
                        :class="currentPage >= totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'"
                        class="px-3 py-1 rounded border">
                    下一页
                </button>
            </div>
        </div>
    `
};
