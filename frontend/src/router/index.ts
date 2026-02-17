import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layouts/Layout.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Layout,
      children: [
        { path: '', name: 'home', component: () => import('../views/HomeView.vue') },
        {
          path: 'projects/:id',
          name: 'project',
          component: () => import('../views/ProjectView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/tests/:testId',
          name: 'test',
          component: () => import('../views/TestView.vue'),
          props: true,
        },
      ],
    },
  ],
})
