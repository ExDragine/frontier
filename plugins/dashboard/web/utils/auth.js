// 认证工具：管理 JWT token
const AuthUtils = {
    TOKEN_KEY: 'frontier_dashboard_token',
    
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },
    
    removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    },
    
    isLoggedIn() {
        const token = this.getToken();
        if (!token) return false;
        
        // 简单检查 token 是否过期（解析 JWT payload）
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 > Date.now();
        } catch (e) {
            return false;
        }
    },
    
    logout() {
        this.removeToken();
        window.location.hash = '#/login';
    }
};
