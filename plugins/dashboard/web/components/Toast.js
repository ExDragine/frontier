// Toast 通知组件
const toastState = Vue.reactive({
    toasts: []
});

let toastId = 0;

window.showToast = function(message, type = 'info') {
    const id = toastId++;
    toastState.toasts.push({ id, message, type });
    setTimeout(() => {
        const index = toastState.toasts.findIndex(t => t.id === id);
        if (index > -1) toastState.toasts.splice(index, 1);
    }, 3000);
};

const ToastComponent = {
    template: `
        <div class="fixed top-4 right-4 z-50 space-y-2">
            <div v-for="toast in toasts" :key="toast.id"
                 :class="toastClass(toast.type)"
                 class="px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 min-w-[300px] animate-fade-in">
                <span>{{ toast.message }}</span>
            </div>
        </div>
    `,
    setup() {
        return {
            toasts: toastState.toasts,
            toastClass(type) {
                const base = 'text-white';
                if (type === 'success') return `${base} bg-green-500`;
                if (type === 'error') return `${base} bg-red-500`;
                if (type === 'warning') return `${base} bg-yellow-500`;
                return `${base} bg-blue-500`;
            }
        };
    }
};
