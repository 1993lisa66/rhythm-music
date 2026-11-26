<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  initialTitle: { type: String, default: '' },
  initialDesc: { type: String, default: '' },
  submitting: { type: Boolean, default: false }
})

const emit = defineEmits(['submit', 'close'])

const ready = ref(false)
const title = ref('')
const desc = ref('')
const inputRef = ref(null)

onMounted(() => {
  ready.value = true
})

/* 每次打开都回填当前值，避免沿用上一次的输入 */
watch(
  () => props.open,
  (open) => {
    if (!open) return
    title.value = props.initialTitle
    desc.value = props.initialDesc
    nextTick(() => inputRef.value?.focus())
  }
)

const canSubmit = () => title.value.trim().length > 0 && !props.submitting

const submit = () => {
  if (!canSubmit()) return
  emit('submit', { title: title.value.trim(), desc: desc.value.trim() })
}
</script>

<template>
  <Teleport v-if="ready" to=".device">
    <transition name="scrim">
      <div v-if="open" class="scrim" @click.self="emit('close')">
        <div
          class="sheet"
          role="dialog"
          aria-modal="true"
          :aria-label="mode === 'create' ? '新建歌单' : '编辑歌单'"
        >
          <span class="grip" aria-hidden="true"></span>
          <p class="title">{{ mode === 'create' ? '新建歌单' : '编辑歌单' }}</p>

          <label class="field">
            <span class="field__label">歌单名称</span>
            <input
              ref="inputRef"
              v-model="title"
              class="field__input"
              type="text"
              maxlength="60"
              placeholder="给歌单起个名字"
              @keyup.enter="submit"
            />
          </label>

          <label class="field">
            <span class="field__label">简介（可选）</span>
            <textarea
              v-model="desc"
              class="field__area"
              maxlength="300"
              rows="2"
              placeholder="一句话描述这个歌单"
            ></textarea>
          </label>

          <button type="button" class="submit" :disabled="!canSubmit()" @click="submit">
            {{ submitting ? '保存中…' : mode === 'create' ? '创建歌单' : '保存修改' }}
          </button>
          <button type="button" class="cancel" @click="emit('close')">取消</button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.scrim {
  position: absolute;
  inset: 0;
  z-index: 76;
  background: rgba(43, 31, 26, 0.32);
  display: flex;
  align-items: flex-end;
  backdrop-filter: blur(2px);
}

.sheet {
  width: 100%;
  padding: 10px 16px calc(18px + env(safe-area-inset-bottom));
  border-radius: 28px 28px 0 0;
  background: #fffdf8;
  box-shadow: 0 -12px 40px rgba(43, 31, 26, 0.2);
}

.grip {
  display: block;
  width: 40px;
  height: 4px;
  margin: 0 auto 12px;
  border-radius: 2px;
  background: var(--surface-soft);
}

.title {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--ink);
  text-align: center;
}

.field {
  display: block;
  margin-top: 14px;
}

.field__label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
}

.field__input,
.field__area {
  width: 100%;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--surface-soft);
  font-size: 15px;
  line-height: 20px;
  color: var(--ink);
}

.field__input::placeholder,
.field__area::placeholder {
  color: var(--placeholder);
}

.field__area {
  display: block;
  resize: none;
  font-family: inherit;
}

.submit {
  width: 100%;
  height: 50px;
  margin-top: 18px;
  border-radius: 18px;
  background: var(--primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  box-shadow: var(--shadow-cta);
  transition: transform 0.16s ease, opacity 0.16s ease;
}

.submit:active {
  transform: scale(0.99);
}

.submit:disabled {
  opacity: 0.42;
  box-shadow: none;
}

.cancel {
  width: 100%;
  height: 48px;
  margin-top: 10px;
  border-radius: 18px;
  background: var(--surface-soft);
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-sub);
}

.cancel:active {
  background: rgba(43, 31, 26, 0.06);
}

.scrim-enter-active,
.scrim-leave-active {
  transition: opacity 0.2s ease;
}

.scrim-enter-from,
.scrim-leave-to {
  opacity: 0;
}

.scrim-enter-active .sheet,
.scrim-leave-active .sheet {
  transition: transform 0.26s cubic-bezier(0.32, 0.72, 0, 1);
}

.scrim-enter-from .sheet,
.scrim-leave-to .sheet {
  transform: translateY(100%);
}
</style>
