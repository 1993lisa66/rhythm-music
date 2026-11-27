<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import { login, register, lastEmail } from '@/store/auth'
import { loadAll, resetData } from '@/store/data'
import { syncPlayer } from '@/store/player'
import { loadSettings } from '@/store/settings'

const router = useRouter()
const route = useRoute()

const mode = ref('login')
const email = ref(lastEmail())
const password = ref('')
const name = ref('')
const error = ref('')
const busy = ref(false)
const showPassword = ref(false)

const isRegister = computed(() => mode.value === 'register')
const canSubmit = computed(
  () => email.value.trim().length > 3 && password.value.length >= 6 && !busy.value
)
const submitText = computed(() => {
  if (busy.value) return isRegister.value ? '正在创建…' : '正在登录…'
  return isRegister.value ? '创建账号并进入' : '登录'
})

const switchMode = (next) => {
  if (mode.value === next) return
  mode.value = next
  error.value = ''
}

const fillDemo = () => {
  mode.value = 'login'
  email.value = 'demo@rhythm.app'
  password.value = 'rhythm2026'
  error.value = ''
}

const submit = async () => {
  if (!canSubmit.value) {
    error.value =
      password.value.length < 6 ? '密码至少 6 位' : '请填写有效的邮箱地址'
    return
  }
  busy.value = true
  error.value = ''
  try {
    if (isRegister.value) await register(email.value.trim(), password.value, name.value.trim())
    else await login(email.value.trim(), password.value)

    // 换了账号就重建数据与播放态，避免看到上一个账号的缓存
    resetData()
    await Promise.all([loadAll(), syncPlayer(), loadSettings()])

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/discover'
    router.replace(redirect)
  } catch (err) {
    error.value = err?.message || '登录失败，请稍后再试'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page login">
    <div class="login__glow" aria-hidden="true"></div>

    <div class="brand">
      <span class="brand__logo">
        <Icon name="note" :size="26" :stroke="1.8" />
      </span>
      <h1 class="brand__name">韵律</h1>
      <p class="brand__slogan">把喜欢的音乐，留在自己的节奏里</p>
    </div>

    <div class="tabs" role="tablist" aria-label="登录或注册">
      <button
        type="button"
        role="tab"
        class="tabs__item"
        :class="{ 'tabs__item--on': mode === 'login' }"
        :aria-selected="mode === 'login'"
        @click="switchMode('login')"
      >
        登录
      </button>
      <button
        type="button"
        role="tab"
        class="tabs__item"
        :class="{ 'tabs__item--on': mode === 'register' }"
        :aria-selected="mode === 'register'"
        @click="switchMode('register')"
      >
        注册
      </button>
    </div>

    <form class="form" @submit.prevent="submit">
      <label v-if="isRegister" class="field">
        <span class="field__label">昵称</span>
        <div class="field__box">
          <Icon class="field__icon" name="user" :size="18" :stroke="1.7" />
          <input
            v-model="name"
            class="field__input"
            type="text"
            maxlength="20"
            placeholder="怎么称呼你（可留空）"
            autocomplete="nickname"
          />
        </div>
      </label>

      <label class="field">
        <span class="field__label">邮箱</span>
        <div class="field__box">
          <Icon class="field__icon" name="mail" :size="18" :stroke="1.7" />
          <input
            v-model="email"
            class="field__input"
            type="email"
            inputmode="email"
            placeholder="you@example.com"
            autocomplete="email"
          />
        </div>
      </label>

      <label class="field">
        <span class="field__label">密码</span>
        <div class="field__box">
          <Icon class="field__icon" name="lock" :size="18" :stroke="1.7" />
          <input
            v-model="password"
            class="field__input"
            :type="showPassword ? 'text' : 'password'"
            :placeholder="isRegister ? '至少 6 位' : '请输入密码'"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
          />
          <button
            type="button"
            class="field__eye"
            :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            @click="showPassword = !showPassword"
          >
            <Icon :name="showPassword ? 'eyeOff' : 'eye'" :size="17" :stroke="1.7" />
          </button>
        </div>
      </label>

      <p v-if="error" class="error" role="alert">
        <Icon name="info" :size="15" :stroke="1.9" />
        {{ error }}
      </p>

      <button type="submit" class="submit" :disabled="busy">
        {{ submitText }}
      </button>
    </form>

    <div class="demo">
      <p class="demo__text">演示账号 <span class="demo__id num">demo@rhythm.app</span> / 密码 <span class="demo__id num">rhythm2026</span></p>
      <button type="button" class="demo__btn" @click="fillDemo">一键填入演示账号</button>
    </div>
  </div>
</template>

<style scoped>
.login {
  padding: 76px 28px 40px;
}

.login__glow {
  position: absolute;
  left: 50%;
  top: -120px;
  width: 320px;
  height: 320px;
  margin-left: -160px;
  border-radius: 50%;
  background: var(--sunset);
  opacity: 0.16;
  filter: blur(46px);
  pointer-events: none;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.brand__logo {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  background: var(--sunset);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-glow);
  margin-bottom: 6px;
}

.brand__name {
  font-size: 30px;
  font-weight: 700;
  line-height: 38px;
  letter-spacing: 4px;
  color: var(--ink);
}

.brand__slogan {
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}

.tabs {
  margin-top: 30px;
  height: 46px;
  padding: 4px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(224, 120, 86, 0.09);
  display: flex;
  gap: 4px;
}

.tabs__item {
  flex: 1 1 0;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-sub);
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.tabs__item--on {
  background: var(--surface);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(43, 31, 26, 0.08);
}

.form {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field__label {
  padding-left: 2px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 600;
  letter-spacing: 0.4px;
  color: var(--ink-sub);
}

/* 输入框：白瓷胶囊 + 细描边；焦点态由容器整体表达（描边变主色 + 柔光），
   内部 input 不再画任何框 */
.field__box {
  position: relative;
  height: 54px;
  padding: 0 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  border: 1.5px solid rgba(224, 120, 86, 0.1);
  box-shadow: 0 1px 2px rgba(43, 31, 26, 0.03), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  gap: 11px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.field__box:focus-within {
  background: #fff;
  border-color: rgba(224, 120, 86, 0.55);
  box-shadow: 0 6px 20px rgba(224, 120, 86, 0.16), 0 0 0 4px rgba(224, 120, 86, 0.1);
}

.field__icon {
  color: var(--placeholder);
  flex: 0 0 auto;
  transition: color 0.2s ease;
}

.field__box:focus-within .field__icon {
  color: var(--primary);
}

/* 16px：iOS 上小于 16px 的表单控件聚焦会自动放大页面 */
.field__input {
  flex: 1 1 auto;
  min-width: 0;
  height: 100%;
  font-size: 16px;
  line-height: 20px;
  letter-spacing: 0.1px;
  color: var(--ink);
  outline: 0;
  box-shadow: none;
  background: transparent;
}

.field__input::placeholder {
  color: #c3b6a9;
  font-size: 15px;
}

.field__eye {
  width: 40px;
  height: 40px;
  margin-right: -8px;
  border-radius: 12px;
  color: var(--placeholder);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  transition: color 0.18s ease, background 0.18s ease;
}

.field__eye:active {
  background: rgba(224, 120, 86, 0.08);
  color: var(--primary);
}

.error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(196, 84, 63, 0.1);
  color: #c4543f;
  font-size: 12px;
  line-height: 16px;
}

.submit {
  height: 54px;
  margin-top: 6px;
  border-radius: 16px;
  background: var(--sunset);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  box-shadow: var(--shadow-cta);
  transition: transform 0.16s ease, opacity 0.16s ease, box-shadow 0.16s ease;
}

.submit:not(:disabled):hover {
  box-shadow: 0 12px 28px rgba(224, 120, 86, 0.34);
}

.submit:active {
  transform: scale(0.985);
}

.submit:disabled {
  opacity: 0.6;
  cursor: default;
}

.demo {
  margin-top: auto;
  padding-top: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.demo__text {
  font-size: 11px;
  line-height: 15px;
  color: var(--placeholder);
}

.demo__id {
  color: var(--ink-sub);
}

.demo__btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 19px;
  border: 1.5px solid rgba(224, 120, 86, 0.45);
  color: var(--primary);
  font-size: 12.5px;
  font-weight: 600;
  transition: border-color 0.18s ease, background 0.18s ease;
}

.demo__btn:active {
  background: rgba(224, 120, 86, 0.08);
  border-color: var(--primary);
}
</style>
