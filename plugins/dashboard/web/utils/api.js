// API 客户端：封装 fetch 请求
const ApiClient = {
    baseUrl: '/api/dashboard',
    
    async request(method, path, body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = AuthUtils.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const opts = { method, headers };
        if (body) opts.body = JSON.stringify(body);
        
        const response = await fetch(`${this.baseUrl}${path}`, opts);
        
        if (response.status === 401) {
            AuthUtils.logout();
            throw new Error('未授权，请重新登录');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: '请求失败' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    delete(path) { return this.request('DELETE', path); },
};
