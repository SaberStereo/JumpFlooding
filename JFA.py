import numpy as np
import taichi as ti
import taichi_glsl as ts

ti.init()


@ti.data_oriented
class jfa_solver_2D:
    def __init__(self, width, height, sites):
        self.w = width
        self.h = height
        # number of site
        self.num_site = sites.shape[0]
        # store site indices
        self.pixels = ti.field(ti.i32, (self.w, self.h))
        # store site position
        self.sites = ti.Vector(sites.shape[1], ti.f32, sites.shape[0])
        # discretize site
        self.sites.from_numpy(sites)

    @ti.kernel
    def init_sites(self):
        for i, j in self.pixels:
            self.pixels[i, j] = -1
        for i in range(self.num_site):
            index = ti.cast(
                ts.vec(self.sites[i].x * self.w, self.sites[i].y * self.h), ti.i32)
            # 1+JFA
            for x, y in ti.ndrange((-1, 2), (-1, 2)):
                index_off = ts.vec(index.x + x, index.y + y)
                if 0 <= index_off.x < self.w and 0 <= index_off.y < self.h:
                    self.pixels[index_off] = i

    @ti.kernel
    def assign_sites(self, new_sites: ti.template()):
        for i in range(self.num_site):
            self.sites[i].x = new_sites[i].x
            self.sites[i].y = new_sites[i].y

    @ti.kernel
    def jfa_step(self, step_x: ti.i32, step_y: ti.i32):
        for i, j in self.pixels:
            min_distance = 1e10
            min_index = -1
            for x, y in ti.ndrange((-1, 2), (-1, 2)):
                ix = i+x*step_x
                jy = j+y*step_y
                if 0 <= ix < self.w and 0 <= jy < self.h:
                    if self.pixels[ix, jy] != -1:
                        dist = ts.distance(ts.vec(i/self.w, j/self.h), ts.vec(
                            self.sites[self.pixels[ix, jy]]))
                        if dist < min_distance:
                            min_distance = dist
                            min_index = self.pixels[ix, jy]
            self.pixels[i, j] = min_index

    def solve_jfa(self, init_step):
        self.init_sites()
        step_x = init_step[0]
        step_y = init_step[1]
        while True:
            self.jfa_step(step_x, step_y)
            step_x = step_x // 2
            step_y = step_y // 2
            if step_x == 0 and step_y == 0:
                break
            else:
                step_x = 1 if step_x < 1 else step_x
                step_y = 1 if step_y < 1 else step_y

    @ ti.kernel
    def render_color(self, screen: ti.template(), site_info: ti.template()):
        for I in ti.grouped(screen):
            if self.pixels[I] != -1:
                screen[I] = site_info[self.pixels[I]]
            else:
                screen[I].fill(-1)

    def debug_sites(self):
        seed_np = self.sites.to_numpy()
        return seed_np[:self.num_site]


@ti.data_oriented
class jfa_solver_3D:
    def __init__(self, width, height, length, sites):
        self.w = width
        self.h = height
        self.l = length
        self.num_site = sites.shape[0]
        self.pixels = ti.field(ti.i32, shape=(self.w, self.h, self.l))
        self.sites = ti.Vector(sites.shape[1], ti.f32, sites.shape[0])
        self.sites.from_numpy(sites)

    @ti.kernel
    def init_sites(self):
        for i, j, k in self.pixels:
            self.pixels[i, j, k] = -1
        for i in range(self.num_site):
            index = ti.cast(
                ts.vec(self.sites[i].x * self.w, self.sites[i].y * self.h, self.sites[i].z * self.l), ti.i32)
            # 1+JFA
            for x, y, z in ti.ndrange((-1, 2), (-1, 2), (-1, 2)):
                index_off = ts.vec(index.x + x, index.y + y, index.z + z)
                if 0 <= index_off.x < self.w and 0 <= index_off.y < self.h and 0 <= index_off.z < self.l:
                    self.pixels[index_off] = i

    @ti.kernel
    def jfa_step(self, step_x: ti.i32, step_y: ti.i32, step_z: ti.i32):
        for i, j, k in self.pixels:
            min_distance = 1e10
            min_index = -1
            for x, y, z in ti.ndrange((-1, 2), (-1, 2), (-1, 2)):
                ix = i+x*step_x
                jy = j+y*step_y
                kz = k+z*step_z
                if 0 <= ix < self.w and 0 <= jy < self.h and 0 <= kz < self.l:
                    if self.pixels[ix, jy, kz] != -1:
                        dist = ts.distance(ts.vec(i/self.w, j/self.h, k/self.l), ts.vec(
                            self.sites[self.pixels[ix, jy, kz]]))
                        if dist < min_distance:
                            min_distance = dist
                            min_index = self.pixels[ix, jy, kz]
            self.pixels[i, j, k] = min_index

    def solve_jfa(self, init_step):
        self.init_sites()
        step_x = init_step[0]
        step_y = init_step[1]
        step_z = init_step[2]
        while True:
            self.jfa_step(step_x, step_y, step_z)
            step_x = step_x // 2
            step_y = step_y // 2
            step_z = step_z // 2
            if step_x == 0 and step_y == 0 and step_z == 0:
                break
            else:
                step_x = 1 if step_x < 1 else step_x
                step_y = 1 if step_y < 1 else step_y
                step_z = 1 if step_z < 1 else step_z

    @ti.kernel
    def debug_slice(self, screen: ti.template(), site_info: ti.template(), slice: ti.i32):
        for i, j in ti.ndrange((0, self.w), (0, self.h)):
            if self.pixels[i, j, slice] != -1:
                screen[i, j] = site_info[self.pixels[i, j, slice]]
            else:
                screen[i, j].fill(-1)
