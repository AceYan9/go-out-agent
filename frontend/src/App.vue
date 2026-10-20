<template>
  <div>
    <el-container>
      <el-aside width="15%"></el-aside>
      <el-main><router-view /></el-main>
      <el-aside width="15%"></el-aside>
    </el-container>
  </div>
</template>

<style>

/* 根布局：严格占满视口 */
.chat-page {
  position: fixed;
  inset: 0;

  display: flex;
  flex-direction: column;

  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;

  overflow: hidden;
  background: #f3f8ff;
  color: #25344b;
}

/* 顶部：固定 64px */
.chat-header {
  flex: 0 0 64px;
  height: 64px;
  min-height: 64px;
}

/* 中间：占用所有剩余空间 */
.chat-history {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;

  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;

  padding: 24px;
}

/* 底部：自然高度，始终位于容器底部 */
.chat-footer {
  flex: 0 0 auto;
  width: 100%;
  min-width: 0;
  margin-top: auto;

  padding: 14px 24px calc(12px + env(safe-area-inset-bottom));
  background: #f3f8ff;
}

</style>
