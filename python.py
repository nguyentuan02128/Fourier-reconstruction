from manimlib.imports import *
# import scipy


class FourierCirclesScene(Scene):
    CONFIG = {
        "n_vectors": 10,
        "big_radius": 2,
        "colors": [
            BLUE_D,
            BLUE_C,
            BLUE_E,
            GREY_BROWN,
        ],
        "circle_style": {
            "stroke_width": 2,
        },
        "vector_config": {
            "buff": 0,
            "max_tip_length_to_length_ratio": 0.35,
            "tip_length": 0.15,
            "max_stroke_width_to_length_ratio": 10,
            "stroke_width": 2,
        },
        "circle_config": {
            "stroke_width": 1,
        },
        "base_frequency": 1,
        "slow_factor": 0.25,
        "center_point": ORIGIN,
        "parametric_function_step_size": 0.001,
        "drawn_path_color": YELLOW,
        "drawn_path_stroke_width": 2,
    }

    def setup(self):
        self.slow_factor_tracker = ValueTracker(
            self.slow_factor
        )
        self.vector_clock = ValueTracker(0)
        self.vector_clock.add_updater(
            lambda m, dt: m.increment_value(
                self.get_slow_factor() * dt
            )
        )
        self.add(self.vector_clock)

    def get_slow_factor(self):
        return self.slow_factor_tracker.get_value()

    def get_vector_time(self):
        return self.vector_clock.get_value()

    #
    def get_freqs(self):
        n = self.n_vectors
        all_freqs = list(range(n // 2, -n // 2, -1))
        all_freqs.sort(key=abs)
        return all_freqs

    def get_coefficients(self):
        return [complex(0) for x in range(self.n_vectors)]

    def get_color_iterator(self):
        return it.cycle(self.colors)

    def get_rotating_vectors(self, freqs=None, coefficients=None):
        vectors = VGroup()
        self.center_tracker = VectorizedPoint(self.center_point)

        if freqs is None:
            freqs = self.get_freqs()
        if coefficients is None:
            coefficients = self.get_coefficients()

        last_vector = None
        for freq, coefficient in zip(freqs, coefficients):
            if last_vector:
                center_func = last_vector.get_end
            else:
                center_func = self.center_tracker.get_location
            vector = self.get_rotating_vector(
                coefficient=coefficient,
                freq=freq,
                center_func=center_func,
            )
            vectors.add(vector)
            last_vector = vector
        return vectors

    def get_rotating_vector(self, coefficient, freq, center_func):
        vector = Vector(RIGHT, **self.vector_config)
        vector.scale(abs(coefficient))
        if abs(coefficient) == 0:
            phase = 0
        else:
            phase = np.log(coefficient).imag
        vector.rotate(phase, about_point=ORIGIN)
        vector.freq = freq
        vector.coefficient = coefficient
        vector.center_func = center_func
        vector.add_updater(self.update_vector)
        return vector

    def update_vector(self, vector, dt):
        time = self.get_vector_time()
        coef = vector.coefficient
        freq = vector.freq
        phase = np.log(coef).imag

        vector.set_length(abs(coef))
        vector.set_angle(phase + time * freq * TAU)
        vector.shift(vector.center_func() - vector.get_start())
        return vector

    def get_circles(self, vectors):
        return VGroup(*[
            self.get_circle(
                vector,
                color=color
            )
            for vector, color in zip(
                vectors,
                self.get_color_iterator()
            )
        ])

    def get_circle(self, vector, color=BLUE):
        circle = Circle(color=color, **self.circle_config)
        circle.center_func = vector.get_start
        circle.radius_func = vector.get_length
        circle.add_updater(self.update_circle)
        return circle

    def update_circle(self, circle):
        circle.set_width(2 * circle.radius_func())
        circle.move_to(circle.center_func())
        return circle

    def get_vector_sum_path(self, vectors, color=YELLOW):
        coefs = [v.coefficient for v in vectors]
        freqs = [v.freq for v in vectors]
        center = vectors[0].get_start()

        path = ParametricFunction(
            lambda t: center + reduce(op.add, [
                complex_to_R3(
                    coef * np.exp(TAU * 1j * freq * t)
                )
                for coef, freq in zip(coefs, freqs)
            ]),
            t_min=0,
            t_max=1,
            color=color,
            step_size=self.parametric_function_step_size,
        )
        return path

    # TODO, this should be a general animated mobect
    def get_drawn_path_alpha(self):
        return self.get_vector_time()

    def get_drawn_path(self, vectors, stroke_width=None, **kwargs):
        if stroke_width is None:
            stroke_width = self.drawn_path_stroke_width
        path = self.get_vector_sum_path(vectors, **kwargs)
        broken_path = CurvesAsSubmobjects(path)
        broken_path.curr_time = 0

        def update_path(path, dt):
            # alpha = path.curr_time * self.get_slow_factor()
            alpha = self.get_drawn_path_alpha()
            n_curves = len(path)
            for a, sp in zip(np.linspace(0, 1, n_curves), path):
                b = alpha - a
                if b < 0:
                    width = 0
                else:
                    width = stroke_width * (1 - (b % 1))
                sp.set_stroke(width=width)
            path.curr_time += dt
            return path

        broken_path.set_color(self.drawn_path_color)
        broken_path.add_updater(update_path)
        return broken_path

    def get_y_component_wave(self,
                             vectors,
                             left_x=1,
                             color=PINK,
                             n_copies=2,
                             right_shift_rate=5):
        path = self.get_vector_sum_path(vectors)
        wave = ParametricFunction(
            lambda t: op.add(
                right_shift_rate * t * LEFT,
                path.function(t)[1] * UP
            ),
            t_min=path.t_min,
            t_max=path.t_max,
            color=color,
        )
        wave_copies = VGroup(*[
            wave.copy()
            for x in range(n_copies)
        ])
        wave_copies.arrange(RIGHT, buff=0)
        top_point = wave_copies.get_top()
        wave.creation = ShowCreation(
            wave,
            run_time=(1 / self.get_slow_factor()),
            rate_func=linear,
        )
        cycle_animation(wave.creation)
        wave.add_updater(lambda m: m.shift(
            (m.get_left()[0] - left_x) * LEFT
        ))

        def update_wave_copies(wcs):
            index = int(
                wave.creation.total_time * self.get_slow_factor()
            )
            wcs[:index].match_style(wave)
            wcs[index:].set_stroke(width=0)
            wcs.next_to(wave, RIGHT, buff=0)
            wcs.align_to(top_point, UP)
        wave_copies.add_updater(update_wave_copies)

        return VGroup(wave, wave_copies)

    def get_wave_y_line(self, vectors, wave):
        return DashedLine(
            vectors[-1].get_end(),
            wave[0].get_end(),
            stroke_width=1,
            dash_length=DEFAULT_DASH_LENGTH * 0.5,
        )

    # Computing Fourier series
    # i.e. where all the math happens
    def get_coefficients_of_path(self, path, n_samples=10000, freqs=None):
        if freqs is None:
            freqs = self.get_freqs()
        dt = 1 / n_samples
        ts = np.arange(0, 1, dt)
        samples = np.array([
            path.point_from_proportion(t)
            for t in ts
        ])
        samples -= self.center_point
        complex_samples = samples[:, 0] + 1j * samples[:, 1]

        result = []
        for freq in freqs:
            riemann_sum = np.array([
                np.exp(-TAU * 1j * freq * t) * cs
                for t, cs in zip(ts, complex_samples)
            ]).sum() * dt
            result.append(riemann_sum)

        return result


class FourierSeriesIntroBackground4(FourierCirclesScene):
    CONFIG = {
        "n_vectors": 4,
        "center_point": 4 * LEFT,
        "run_time": 30,
        "big_radius": 1.5,
    }

    def construct(self):
        circles = self.get_circles()
        path = self.get_drawn_path(circles)
        wave = self.get_y_component_wave(circles)
        h_line = always_redraw(
            lambda: self.get_wave_y_line(circles, wave)
        )

        # Why?
        circles.update(-1 / self.camera.frame_rate)
        #
        self.add(circles, path, wave, h_line)
        self.wait(self.run_time)

    def get_ks(self):
        return np.arange(1, 2 * self.n_vectors + 1, 2)

    def get_freqs(self):
        return self.base_frequency * self.get_ks()

    def get_coefficients(self):
        return self.big_radius / self.get_ks()


class FourierSeriesIntroBackground8(FourierSeriesIntroBackground4):
    CONFIG = {
        "n_vectors": 8,
    }


class FourierSeriesIntroBackground12(FourierSeriesIntroBackground4):
    CONFIG = {
        "n_vectors": 12,
    }


class FourierSeriesIntroBackground20(FourierSeriesIntroBackground4):
    CONFIG = {
        "n_vectors": 20,
    }


class FourierOfPiSymbol(FourierCirclesScene):
    CONFIG = {
        "n_vectors": 51,
        "center_point": ORIGIN,
        "slow_factor": 0.1,
        "n_cycles": 1,
        "tex": "\\pi",
        "start_drawn": False,
        "max_circle_stroke_width": 1,
    }

    def construct(self):
        self.add_vectors_circles_path()
        for n in range(self.n_cycles):
            self.run_one_cycle()

    def add_vectors_circles_path(self):
        path = self.get_path()
        coefs = self.get_coefficients_of_path(path)
        vectors = self.get_rotating_vectors(coefficients=coefs)
        circles = self.get_circles(vectors)
        self.set_decreasing_stroke_widths(circles)
        # approx_path = self.get_vector_sum_path(circles)
        drawn_path = self.get_drawn_path(vectors)
        if self.start_drawn:
            self.vector_clock.increment_value(1)

        self.add(path)
        self.add(vectors)
        self.add(circles)
        self.add(drawn_path)

        self.vectors = vectors
        self.circles = circles
        self.path = path
        self.drawn_path = drawn_path

    def run_one_cycle(self):
        time = 1 / self.slow_factor
        self.wait(time)

    def set_decreasing_stroke_widths(self, circles):
        mcsw = self.max_circle_stroke_width
        for k, circle in zip(it.count(1), circles):
            circle.set_stroke(width=max(
                # mcsw / np.sqrt(k),
                mcsw / k,
                mcsw,
            ))
        return circles

    def get_path(self):
        tex_mob = TexMobject(self.tex)
        tex_mob.set_height(6)
        path = tex_mob.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        return path


class FourierOfTexPaths(FourierOfPiSymbol, MovingCameraScene):
    CONFIG = {
        "n_vectors": 100,
        "name_color": WHITE,
        "animated_name": "Abc",
        "time_per_symbol": 5,
        "slow_factor": 1 / 5,
        "parametric_function_step_size": 0.01,
    }

    def construct(self):
        name = TextMobject(self.animated_name)
        max_width = FRAME_WIDTH - 2
        max_height = FRAME_HEIGHT - 2
        name.set_width(max_width)
        if name.get_height() > max_height:
            name.set_height(max_height)

        frame = self.camera.frame
        frame.save_state()

        vectors = VGroup(VectorizedPoint())
        circles = VGroup(VectorizedPoint())
        for path in name.family_members_with_points():
            for subpath in path.get_subpaths():
                sp_mob = VMobject()
                sp_mob.set_points(subpath)
                coefs = self.get_coefficients_of_path(sp_mob)
                new_vectors = self.get_rotating_vectors(
                    coefficients=coefs
                )
                new_circles = self.get_circles(new_vectors)
                self.set_decreasing_stroke_widths(new_circles)

                drawn_path = self.get_drawn_path(new_vectors)
                drawn_path.clear_updaters()
                drawn_path.set_stroke(self.name_color, 3)

                static_vectors = VMobject().become(new_vectors)
                static_circles = VMobject().become(new_circles)
                # static_circles = new_circles.deepcopy()
                # static_vectors.clear_updaters()
                # static_circles.clear_updaters()

                self.play(
                    Transform(vectors, static_vectors, remover=True),
                    Transform(circles, static_circles, remover=True),
                    frame.set_height, 1.5 * name.get_height(),
                    frame.move_to, path,
                )

                self.add(new_vectors, new_circles)
                self.vector_clock.set_value(0)
                self.play(
                    ShowCreation(drawn_path),
                    rate_func=linear,
                    run_time=self.time_per_symbol
                )
                self.remove(new_vectors, new_circles)
                self.add(static_vectors, static_circles)

                vectors = static_vectors
                circles = static_circles
        self.play(
            FadeOut(vectors),
            Restore(frame),
            run_time=2
        )
        self.wait(3)


class FourierOfPiSymbol5(FourierOfPiSymbol):
    CONFIG = {
        "n_vectors": 5,
        "run_time": 10,
    }


class FourierOfTrebleClef(FourierOfPiSymbol):
    CONFIG = {
        "n_vectors": 101,
        "run_time": 10,
        "start_drawn": True,
        "file_name": "TrebleClef",
        "height": 7.5,
    }

    def get_shape(self):
        shape = SVGMobject(self.file_name)
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path


class FourierOfIP(FourierOfTrebleClef):
    CONFIG = {
        "file_name": "IP_logo2",
        "height": 6,
        "n_vectors": 100,
    }

    # def construct(self):
    #     path = self.get_path()
    #     self.add(path)

    def get_shape(self):
        shape = SVGMobject(self.file_name)
        return shape

    def get_path(self):
        shape = self.get_shape()
        path = shape.family_members_with_points()[0]
        path.add_line_to(path.get_start())
        # path.make_smooth()

        path.set_height(self.height)
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 0)
        return path


class FourierOfEighthNote(FourierOfTrebleClef):
    CONFIG = {
        "file_name": "EighthNote"
    }


class FourierOfN(FourierOfTrebleClef):
    CONFIG = {
        "height": 6,
        "n_vectors": 1000,
    }

    def get_shape(self):
        return TexMobject("N")


class FourierNailAndGear(FourierOfTrebleClef):
    CONFIG = {
        "height": 6,
        "n_vectors": 200,
        "run_time": 100,
        "slow_factor": 0.01,
        "parametric_function_step_size": 0.0001,
        "arrow_config": {
            "tip_length": 0.1,
            "stroke_width": 2,
        }
    }

    def get_shape(self):
        shape = SVGMobject("Nail_And_Gear")[1]
        return shape


class FourierBatman(FourierOfTrebleClef):
    CONFIG = {
        "height": 4,
        "n_vectors": 100,
        "run_time": 10,
        "arrow_config": {
            "tip_length": 0.1,
            "stroke_width": 2,
        }
    }

    def get_shape(self):
        shape = SVGMobject("BatmanLogo")[1]
        return shape


class FourierHeart(FourierOfTrebleClef):
    CONFIG = {
        "height": 4,
        "n_vectors": 100,
        "run_time": 10,
        "arrow_config": {
            "tip_length": 0.1,
            "stroke_width": 2,
        }
    }

    def get_shape(self):
        shape = SuitSymbol("hearts")
        return shape

    def get_drawn_path(self, *args, **kwargs):
        kwargs["stroke_width"] = 5
        path = super().get_drawn_path(*args, **kwargs)
        path.set_color(PINK)
        return path


class FourierNDQ(FourierOfTrebleClef):
    CONFIG = {
        "height": 4,
        "n_vectors": 1000,
        "run_time": 10,
        "arrow_config": {
            "tip_length": 0.1,
            "stroke_width": 2,
        }
    }

    def get_shape(self):
        path = VMobject()
        shape = TexMobject("NDQ")
        for sp in shape.family_members_with_points():
            path.append_points(sp.points)
        return path


class FourierGoogleG(FourierOfTrebleClef):
    CONFIG = {
        "n_vectors": 10,
        "height": 5,
        "g_colors": [
            "#4285F4",
            "#DB4437",
            "#F4B400",
            "#0F9D58",
        ]
    }

    def get_shape(self):
        g = SVGMobject("google_logo")[5]
        g.center()
        self.add(g)
        return g

    def get_drawn_path(self, *args, **kwargs):
        kwargs["stroke_width"] = 7
        path = super().get_drawn_path(*args, **kwargs)

        blue, red, yellow, green = self.g_colors

        path[:250].set_color(blue)
        path[250:333].set_color(green)
        path[333:370].set_color(yellow)
        path[370:755].set_color(red)
        path[755:780].set_color(yellow)
        path[780:860].set_color(green)
        path[860:].set_color(blue)

        return path


class ExplainCircleAnimations(FourierCirclesScene):
    CONFIG = {
        "n_vectors": 100,
        "center_point": 2 * DOWN,
        "n_top_circles": 9,
        "path_height": 3,
    }

    def construct(self):
        self.add_path()
        self.add_circles()
        self.wait(8)
        self.organize_circles_in_a_row()
        self.show_frequencies()
        self.show_examples_for_frequencies()
        self.show_as_vectors()
        self.show_vector_sum()
        self.tweak_starting_vectors()

    def add_path(self):
        self.path = self.get_path()
        self.add(self.path)

    def add_circles(self):
        coefs = self.get_coefficients_of_path(self.path)
        self.circles = self.get_circles(coefficients=coefs)

        self.add(self.circles)
        self.drawn_path = self.get_drawn_path(self.circles)
        self.add(self.drawn_path)

    def organize_circles_in_a_row(self):
        circles = self.circles
        top_circles = circles[:self.n_top_circles].copy()

        center_trackers = VGroup()
        for circle in top_circles:
            tracker = VectorizedPoint(circle.center_func())
            circle.center_func = tracker.get_location
            center_trackers.add(tracker)
            tracker.freq = circle.freq
            tracker.circle = circle

        center_trackers.submobjects.sort(
            key=lambda m: m.freq
        )
        center_trackers.generate_target()
        right_buff = 1.45
        center_trackers.target.arrange(RIGHT, buff=right_buff)
        center_trackers.target.to_edge(UP, buff=1.25)

        self.add(top_circles)
        self.play(
            MoveToTarget(center_trackers),
            run_time=2
        )
        self.wait(4)

        self.top_circles = top_circles
        self.center_trackers = center_trackers

    def show_frequencies(self):
        center_trackers = self.center_trackers

        freq_numbers = VGroup()
        for ct in center_trackers:
            number = Integer(ct.freq)
            number.next_to(ct, DOWN, buff=1)
            freq_numbers.add(number)
            ct.circle.number = number

        ld, rd = [
            TexMobject("\\dots")
            for x in range(2)
        ]
        ld.next_to(freq_numbers, LEFT, MED_LARGE_BUFF)
        rd.next_to(freq_numbers, RIGHT, MED_LARGE_BUFF)
        freq_numbers.add_to_back(ld)
        freq_numbers.add(rd)

        freq_word = TextMobject("Frequencies")
        freq_word.scale(1.5)
        freq_word.set_color(YELLOW)
        freq_word.next_to(freq_numbers, DOWN, MED_LARGE_BUFF)

        self.play(
            LaggedStartMap(
                FadeInFromDown, freq_numbers
            )
        )
        self.play(
            Write(freq_word),
            LaggedStartMap(
                ShowCreationThenFadeAround, freq_numbers,
            )
        )
        self.wait(2)

        self.freq_numbers = freq_numbers
        self.freq_word = freq_word

    def show_examples_for_frequencies(self):
        top_circles = self.top_circles
        c1, c2, c3 = [
            list(filter(
                lambda c: c.freq == k,
                top_circles
            ))[0]
            for k in (1, 2, 3)
        ]

        neg_circles = VGroup(*filter(
            lambda c: c.freq < 0,
            top_circles
        ))

        for c in [c1, c2, c3, *neg_circles]:
            c.rect = SurroundingRectangle(c)

        self.play(
            ShowCreation(c2.rect),
            WiggleOutThenIn(c2.number),
        )
        self.wait(2)
        self.play(
            ReplacementTransform(c2.rect, c1.rect),
        )
        self.play(FadeOut(c1.rect))
        self.wait()
        self.play(
            ShowCreation(c3.rect),
            WiggleOutThenIn(c3.number),
        )
        self.play(
            FadeOut(c3.rect),
        )
        self.wait(2)
        self.play(
            LaggedStart(*[
                ShowCreationThenFadeOut(c.rect)
                for c in neg_circles
            ])
        )
        self.wait(3)
        self.play(FadeOut(self.freq_word))

    def show_as_vectors(self):
        top_circles = self.top_circles
        top_vectors = self.get_rotating_vectors(top_circles)
        top_vectors.set_color(WHITE)

        original_circles = top_circles.copy()
        self.play(
            FadeIn(top_vectors),
            top_circles.set_opacity, 0,
        )
        self.wait(3)
        self.play(
            top_circles.match_style, original_circles
        )
        self.remove(top_vectors)

        self.top_vectors = top_vectors

    def show_vector_sum(self):
        trackers = self.center_trackers.copy()
        trackers.sort(
            submob_func=lambda t: abs(t.circle.freq - 0.1)
        )
        plane = self.plane = NumberPlane(
            x_min=-3,
            x_max=3,
            y_min=-2,
            y_max=2,
            axis_config={
                "stroke_color": LIGHT_GREY,
            }
        )
        plane.set_stroke(width=1)
        plane.fade(0.5)
        plane.move_to(self.center_point)

        self.play(
            FadeOut(self.drawn_path),
            FadeOut(self.circles),
            self.slow_factor_tracker.set_value, 0.05,
        )
        self.add(plane, self.path)
        self.play(FadeIn(plane))

        new_circles = VGroup()
        last_tracker = None
        for tracker in trackers:
            if last_tracker:
                tracker.new_location_func = last_tracker.circle.get_start
            else:
                tracker.new_location_func = lambda: self.center_point

            original_circle = tracker.circle
            tracker.circle = original_circle.copy()
            tracker.circle.center_func = tracker.get_location
            new_circles.add(tracker.circle)

            self.add(tracker, tracker.circle)
            start_point = tracker.get_location()
            self.play(
                UpdateFromAlphaFunc(
                    tracker, lambda t, a: t.move_to(
                        interpolate(
                            start_point,
                            tracker.new_location_func(),
                            a,
                        )
                    ),
                    run_time=2
                )
            )
            tracker.add_updater(lambda t: t.move_to(
                t.new_location_func()
            ))
            self.wait(2)
            last_tracker = tracker

        self.wait(3)

        self.clear()
        self.slow_factor_tracker.set_value(0.1)
        self.add(
            self.top_circles,
            self.freq_numbers,
            self.path,
        )
        self.add_circles()
        for tc in self.top_circles:
            for c in self.circles:
                if c.freq == tc.freq:
                    tc.rotate(
                        angle_of_vector(c.get_start() - c.get_center()) -
                        angle_of_vector(tc.get_start() - tc.get_center())
                    )
        self.wait(10)

    def tweak_starting_vectors(self):
        top_circles = self.top_circles
        circles = self.circles
        path = self.path
        drawn_path = self.drawn_path

        new_path = self.get_new_path()
        new_coefs = self.get_coefficients_of_path(new_path)
        new_circles = self.get_circles(coefficients=new_coefs)

        new_top_circles = VGroup()
        new_top_vectors = VGroup()
        for top_circle in top_circles:
            for circle in new_circles:
                if circle.freq == top_circle.freq:
                    new_top_circle = circle.copy()
                    new_top_circle.center_func = top_circle.get_center
                    new_top_vector = self.get_rotating_vector(
                        new_top_circle
                    )
                    new_top_circles.add(new_top_circle)
                    new_top_vectors.add(new_top_vector)

        self.play(
            self.slow_factor_tracker.set_value, 0,
            FadeOut(drawn_path)
        )
        self.wait()
        self.play(
            ReplacementTransform(top_circles, new_top_circles),
            ReplacementTransform(circles, new_circles),
            FadeOut(path),
            run_time=3,
        )
        new_drawn_path = self.get_drawn_path(
            new_circles, stroke_width=4,
        )
        self.add(new_drawn_path)
        self.slow_factor_tracker.set_value(0.1)
        self.wait(20)

    #
    def configure_path(self, path):
        path.set_stroke(WHITE, 1)
        path.set_fill(BLACK, opacity=1)
        path.set_height(self.path_height)
        path.move_to(self.center_point)
        return path

    def get_path(self):
        tex = TexMobject("f")
        path = tex.family_members_with_points()[0]
        self.configure_path(path)
        return path
        # return Square().set_height(3)

    def get_new_path(self):
        shape = SVGMobject("TrebleClef")
        path = shape.family_members_with_points()[0]
        self.configure_path(path)
        path.scale(1.5, about_edge=DOWN)
        return path
        
class GeneralizeToComplexFunctions(Scene):
    CONFIG = {
        "axes_config": {
            "x_min": 0,
            "x_max": 10,
            "x_axis_config": {
                "stroke_width": 2,
            },
            "y_min": -2.5,
            "y_max": 2.5,
            "y_axis_config": {
                "tick_frequency": 0.25,
                "unit_size": 1.5,
                "include_tip": False,
                "stroke_width": 2,
            },
        },
        "complex_plane_config": {
            "axis_config": {
                "unit_size": 2
            }
        },
    }

    def construct(self):
        self.show_cosine_wave()
        self.transition_to_complex_plane()
        self.add_rotating_vectors_making_cos()

    def show_cosine_wave(self):
        axes = Axes(**self.axes_config)
        axes.shift(2 * LEFT - axes.c2p(0, 0))
        y_axis = axes.y_axis
        y_labels = y_axis.get_number_mobjects(
            *range(-2, 3),
            number_config={"num_decimal_places": 1},
        )

        t_tracker = ValueTracker(0)
        t_tracker.add_updater(lambda t, dt: t.increment_value(dt))
        get_t = t_tracker.get_value

        def func(x):
            return 2 * np.cos(x)

        cos_x_max = 20
        cos_wave = axes.get_graph(func, x_max=cos_x_max)
        cos_wave.set_color(YELLOW)
        shown_cos_wave = cos_wave.copy()
        shown_cos_wave.add_updater(
            lambda m: m.pointwise_become_partial(
                cos_wave, 0,
                np.clip(get_t() / cos_x_max, 0, 1),
            ),
        )

        dot = Dot()
        dot.set_color(PINK)
        dot.add_updater(lambda d: d.move_to(
            y_axis.n2p(func(get_t())),
        ))

        h_line = always_redraw(lambda: Line(
            dot.get_right(),
            shown_cos_wave.get_end(),
            stroke_width=1,
        ))

        real_words = TextMobject(
            "Real number\\\\output"
        )
        real_words.to_edge(LEFT)
        real_words.shift(2 * UP)
        real_arrow = Arrow()
        real_arrow.add_updater(
            lambda m: m.put_start_and_end_on(
                real_words.get_corner(DR),
                dot.get_center(),
            ).scale(0.9),
        )

        self.add(t_tracker)
        self.add(axes)
        self.add(y_labels)
        self.add(shown_cos_wave)
        self.add(dot)
        self.add(h_line)

        self.wait(2)
        self.play(
            FadeInFrom(real_words, RIGHT),
            FadeIn(real_arrow),
        )
        self.wait(5)

        y_axis.generate_target()
        y_axis.target.rotate(-90 * DEGREES)
        y_axis.target.center()
        y_axis.target.scale(2 / 1.5)
        y_labels.generate_target()
        for label in y_labels.target:
            label.next_to(
                y_axis.target.n2p(label.get_value()),
                DOWN, MED_SMALL_BUFF,
            )
        self.play(
            FadeOut(shown_cos_wave),
            FadeOut(axes.x_axis),
            FadeOut(h_line),
        )
        self.play(
            MoveToTarget(y_axis),
            MoveToTarget(y_labels),
            real_words.shift, 2 * RIGHT + UP,
        )
        self.wait()

        self.y_axis = y_axis
        self.y_labels = y_labels
        self.real_words = real_words
        self.real_arrow = real_arrow
        self.dot = dot
        self.t_tracker = t_tracker

    def transition_to_complex_plane(self):
        y_axis = self.y_axis
        y_labels = self.y_labels

        plane = self.get_complex_plane()
        plane_words = plane.label

        self.add(plane, *self.get_mobjects())
        self.play(
            FadeOut(y_labels),
            FadeOut(y_axis),
            ShowCreation(plane),
        )
        self.play(Write(plane_words))
        self.wait()

        self.plane = plane
        self.plane_words = plane_words

    def add_rotating_vectors_making_cos(self):
        plane = self.plane
        real_words = self.real_words
        real_arrow = self.real_arrow
        t_tracker = self.t_tracker
        get_t = t_tracker.get_value

        v1 = Vector(2 * RIGHT)
        v2 = Vector(2 * RIGHT)
        v1.set_color(BLUE)
        v2.set_color(interpolate_color(GREY_BROWN, WHITE, 0.5))
        v1.add_updater(
            lambda v: v.set_angle(get_t())
        )
        v2.add_updater(
            lambda v: v.set_angle(-get_t())
        )
        v1.add_updater(
            lambda v: v.shift(plane.n2p(0) - v.get_start())
        )
        # Change?
        v2.add_updater(
            lambda v: v.shift(plane.n2p(0) - v.get_start())
        )

        ghost_v1 = v1.copy()
        ghost_v1.set_opacity(0.5)
        ghost_v1.add_updater(
            lambda v: v.shift(
                v2.get_end() - v.get_start()
            )
        )

        ghost_v2 = v2.copy()
        ghost_v2.set_opacity(0.5)
        ghost_v2.add_updater(
            lambda v: v.shift(
                v1.get_end() - v.get_start()
            )
        )

        circle = Circle(color=GREY_BROWN)
        circle.set_stroke(width=1)
        circle.set_width(2 * v1.get_length())
        circle.move_to(plane.n2p(0))

        formula = TexMobject(
            # "\\cos(x) ="
            # "{1 \\over 2}e^{ix} +"
            # "{1 \\over 2}e^{-ix}",
            "2\\cos(x) =",
            "e^{ix}", "+", "e^{-ix}",
            tex_to_color_map={
                "e^{ix}": v1.get_color(),
                "e^{-ix}": v2.get_color(),
            }
        )
        formula.next_to(ORIGIN, UP, buff=0.75)
        # formula.add_background_rectangle()
        formula.set_stroke(BLACK, 3, background=True)
        formula.to_edge(LEFT, buff=MED_SMALL_BUFF)
        formula_brace = Brace(formula[1:], UP)
        formula_words = formula_brace.get_text(
            "Sum of\\\\rotations"
        )
        formula_words.set_stroke(BLACK, 3, background=True)

        randy = Randolph()
        randy.to_corner(DL)
        randy.look_at(formula)

        self.play(
            FadeOut(real_words),
            FadeOut(real_arrow),
        )
        self.play(
            FadeIn(v1),
            FadeIn(v2),
            FadeIn(circle),
            FadeIn(ghost_v1),
            FadeIn(ghost_v2),
        )
        self.wait(3)
        self.play(FadeInFromDown(formula))
        self.play(
            GrowFromCenter(formula_brace),
            FadeIn(formula_words),
        )
        self.wait(2)
        self.play(FadeIn(randy))
        self.play(randy.change, "pleading")
        self.play(Blink(randy))
        self.wait()
        self.play(randy.change, "confused")
        self.play(Blink(randy))
        self.wait()
        self.play(FadeOut(randy))
        self.wait(20)

    #
    def get_complex_plane(self):
        plane = ComplexPlane(**self.complex_plane_config)
        plane.add_coordinates()

        plane.label = TextMobject("Complex plane")
        plane.label.scale(1.5)
        plane.label.to_corner(UR, buff=MED_SMALL_BUFF)
        return plane


class ClarifyInputAndOutput(GeneralizeToComplexFunctions):
    CONFIG = {
        "input_space_rect_config": {
            "stroke_color": WHITE,
            "stroke_width": 1,
            "fill_color": DARKER_GREY,
            "fill_opacity": 1,
            "width": 6,
            "height": 2,
        },
    }

    def construct(self):
        self.setup_plane()
        self.setup_input_space()
        self.setup_input_trackers()

        self.describe_input()
        self.describe_output()

    def setup_plane(self):
        plane = self.get_complex_plane()
        plane.sublabel = TextMobject("(Output space)")
        plane.sublabel.add_background_rectangle()
        plane.sublabel.next_to(plane.label, DOWN)
        self.add(plane, plane.label)
        self.plane = plane

    def setup_input_space(self):
        rect = Rectangle(**self.input_space_rect_config)
        rect.to_corner(UL, buff=SMALL_BUFF)

        input_line = self.get_input_line(rect)
        input_words = TextMobject("Input space")
        input_words.next_to(
            rect.get_bottom(), UP,
            SMALL_BUFF,
        )

        self.add(rect)
        self.add(input_line)

        self.input_rect = rect
        self.input_line = input_line
        self.input_words = input_words

    def setup_input_trackers(self):
        plane = self.plane
        input_line = self.input_line
        input_tracker = ValueTracker(0)
        get_input = input_tracker.get_value

        input_dot = Dot()
        input_dot.set_color(PINK)
        f_always(
            input_dot.move_to,
            lambda: input_line.n2p(get_input())
        )

        input_decimal = DecimalNumber()
        input_decimal.scale(0.7)
        always(input_decimal.next_to, input_dot, UP)
        f_always(input_decimal.set_value, get_input)

        path = self.get_path()

        def get_output_point():
            return path.point_from_proportion(
                get_input()
            )

        output_dot = Dot()
        output_dot.match_style(input_dot)
        f_always(output_dot.move_to, get_output_point)

        output_vector = Vector()
        output_vector.set_color(WHITE)
        output_vector.add_updater(
            lambda v: v.put_start_and_end_on(
                plane.n2p(0),
                get_output_point()
            )
        )

        output_decimal = DecimalNumber()
        output_decimal.scale(0.7)
        always(output_decimal.next_to, output_dot, UR, SMALL_BUFF)
        f_always(
            output_decimal.set_value,
            lambda: plane.p2n(get_output_point()),
        )

        self.input_tracker = input_tracker
        self.input_dot = input_dot
        self.input_decimal = input_decimal
        self.path = path
        self.output_dot = output_dot
        self.output_vector = output_vector
        self.output_decimal = output_decimal

    def describe_input(self):
        input_tracker = self.input_tracker

        self.play(FadeInFrom(self.input_words, UP))
        self.play(
            FadeInFromLarge(self.input_dot),
            FadeIn(self.input_decimal),
        )
        for value in 1, 0:
            self.play(
                input_tracker.set_value, value,
                run_time=2
            )
        self.wait()

    def describe_output(self):
        path = self.path
        output_dot = self.output_dot
        output_decimal = self.output_decimal
        input_dot = self.input_dot
        input_tracker = self.input_tracker
        plane = self.plane
        real_line = plane.x_axis.copy()
        real_line.set_stroke(RED, 4)
        real_words = TextMobject("Real number line")
        real_words.next_to(ORIGIN, UP)
        real_words.to_edge(RIGHT)

        traced_path = TracedPath(output_dot.get_center)
        traced_path.match_style(path)

        self.play(
            ShowCreation(real_line),
            FadeInFrom(real_words, DOWN)
        )
        self.play(
            FadeOut(real_line),
            FadeOut(real_words),
        )
        self.play(
            FadeInFrom(plane.sublabel, UP)
        )
        self.play(
            FadeIn(output_decimal),
            TransformFromCopy(input_dot, output_dot),
        )

        kw = {
            "run_time": 10,
            "rate_func": lambda t: smooth(t, 1),
        }
        self.play(
            ApplyMethod(input_tracker.set_value, 1, **kw),
            ShowCreation(path.copy(), remover=True, **kw),
        )
        self.add(path)
        self.add(output_dot)
        self.wait()

        # Flatten to 1d
        real_function_word = TextMobject(
            "Real-valued function"
        )
        real_function_word.next_to(ORIGIN, DOWN, MED_LARGE_BUFF)
        path.generate_target()
        path.target.stretch(0, 1)
        path.target.move_to(plane.n2p(0))

        self.play(
            FadeIn(real_function_word),
            MoveToTarget(path),
        )
        input_tracker.set_value(0)
        self.play(
            input_tracker.set_value, 1,
            **kw
        )

    #
    def get_input_line(self, input_rect):
        input_line = UnitInterval()
        input_line.move_to(input_rect)
        input_line.shift(0.25 * UP)
        input_line.set_width(
            input_rect.get_width() - 1
        )
        input_line.add_numbers(0, 0.5, 1)
        return input_line

    def get_path(self):
        # mob = SVGMobject("BatmanLogo")
        mob = TexMobject("\\pi")
        path = mob.family_members_with_points()[0]
        path.set_height(3.5)
        path.move_to(2 * DOWN, DOWN)
        path.set_stroke(YELLOW, 2)
        path.set_fill(opacity=0)
        return path


class GraphForFlattenedPi(ClarifyInputAndOutput):
    CONFIG = {
        "camera_config": {"background_color": DARKER_GREY},
    }

    def construct(self):
        self.setup_plane()
        plane = self.plane
        self.remove(plane, plane.label)

        path = self.get_path()

        axes = Axes(
            x_min=0,
            x_max=1,
            x_axis_config={
                "unit_size": 7,
                "include_tip": False,
                "tick_frequency": 0.1,
            },
            y_min=-1.5,
            y_max=1.5,
            y_axis_config={
                "include_tip": False,
                "unit_size": 2.5,
                "tick_frequency": 0.5,
            },
        )
        axes.set_width(FRAME_WIDTH - 1)
        axes.set_height(FRAME_HEIGHT - 1, stretch=True)
        axes.center()

        axes.x_axis.add_numbers(
            0.5, 1.0,
            number_config={"num_decimal_places": 1},
        )
        axes.y_axis.add_numbers(
            -1.0, 1.0,
            number_config={"num_decimal_places": 1},
        )

        def func(t):
            return plane.x_axis.p2n(
                path.point_from_proportion(t)
            )

        graph = axes.get_graph(func)
        graph.set_color(PINK)

        v_line = always_redraw(lambda: Line(
            axes.x_axis.n2p(axes.x_axis.p2n(graph.get_end())),
            graph.get_end(),
            stroke_width=1,
        ))

        self.add(axes)
        self.add(v_line)

        kw = {
            "run_time": 10,
            "rate_func": lambda t: smooth(t, 1),
        }
        self.play(ShowCreation(graph, **kw))
        self.wait()


class SimpleComplexExponentExample(ClarifyInputAndOutput):
    CONFIG = {
        "input_space_rect_config": {
            "width": 14,
            "height": 1.5,
        },
        "input_line_config": {
            "unit_size": 0.5,
            "x_min": 0,
            "x_max": 25,
            "stroke_width": 2,
        },
        "input_numbers": range(0, 30, 5),
        "input_tex_args": ["t", "="],
    }

    def construct(self):
        self.setup_plane()
        self.setup_input_space()
        self.setup_input_trackers()
        self.setup_output_trackers()

        # Testing
        time = self.input_line.x_max
        self.play(
            self.input_tracker.set_value, time,
            run_time=time,
            rate_func=linear,
        )

    def setup_plane(self):
        plane = ComplexPlane()
        plane.scale(2)
        plane.add_coordinates()
        plane.shift(DOWN)
        self.plane = plane
        self.add(plane)

    def setup_input_trackers(self):
        input_line = self.input_line
        input_tracker = ValueTracker(0)
        get_input = input_tracker.get_value

        input_tip = ArrowTip(start_angle=-TAU / 4)
        input_tip.scale(0.5)
        input_tip.set_color(PINK)
        f_always(
            input_tip.move_to,
            lambda: input_line.n2p(get_input()),
            lambda: DOWN,
        )

        input_label = VGroup(
            TexMobject(*self.input_tex_args),
            DecimalNumber(),
        )
        input_label[0].set_color_by_tex("t", PINK)
        input_label.scale(0.7)
        input_label.add_updater(
            lambda m: m.arrange(RIGHT, buff=SMALL_BUFF)
        )
        input_label.add_updater(
            lambda m: m[1].set_value(get_input())
        )
        input_label.add_updater(
            lambda m: m.next_to(input_tip, UP, SMALL_BUFF)
        )

        self.input_tracker = input_tracker
        self.input_tip = input_tip
        self.input_label = input_label

        self.add(input_tip, input_label)

    def setup_output_trackers(self):
        plane = self.plane
        get_input = self.input_tracker.get_value

        def get_output():
            return np.exp(complex(0, get_input()))

        def get_output_point():
            return plane.n2p(get_output())

        output_label, static_output_label = [
            TexMobject(
                "e^{i t}" + s,
                tex_to_color_map={"t": PINK},
                background_stroke_width=3,
            )
            for s in ["", "\\approx"]
        ]
        output_label.scale(1.2)
        output_label.add_updater(
            lambda m: m.shift(
                -m.get_bottom() +
                get_output_point() +
                rotate_vector(
                    0.35 * RIGHT,
                    get_input(),
                )
            )
        )

        output_vector = Vector()
        output_vector.set_opacity(0.75)
        output_vector.add_updater(
            lambda m: m.put_start_and_end_on(
                plane.n2p(0), get_output_point(),
            )
        )

        t_max = 40
        full_output_path = ParametricFunction(
            lambda t: plane.n2p(np.exp(complex(0, t))),
            t_min=0,
            t_max=t_max
        )
        output_path = VMobject()
        output_path.set_stroke(YELLOW, 2)
        output_path.add_updater(
            lambda m: m.pointwise_become_partial(
                full_output_path,
                0, get_input() / t_max,
            )
        )

        static_output_label.next_to(plane.c2p(1, 1), UR)
        output_decimal = DecimalNumber(
            include_sign=True,
        )
        output_decimal.scale(0.8)
        output_decimal.set_stroke(BLACK, 3, background=True)
        output_decimal.add_updater(
            lambda m: m.set_value(get_output())
        )
        output_decimal.add_updater(
            lambda m: m.next_to(
                static_output_label,
                RIGHT, 2 * SMALL_BUFF,
                aligned_edge=DOWN,
            )
        )

        self.add(output_path)
        self.add(output_vector)
        self.add(output_label)
        self.add(static_output_label)
        self.add(BackgroundRectangle(output_decimal))
        self.add(output_decimal)

    #
    def get_input_line(self, input_rect):
        input_line = NumberLine(**self.input_line_config)
        input_line.move_to(input_rect)
        input_line.set_width(
            input_rect.get_width() - 1.5,
            stretch=True,
        )
        input_line.add_numbers(*self.input_numbers)
        return input_line


class TRangingFrom0To1(SimpleComplexExponentExample):
    CONFIG = {
        "input_space_rect_config": {
            "width": 6,
            "height": 2,
        },
    }

    def construct(self):
        self.setup_input_space()
        self.setup_input_trackers()

        self.play(
            self.input_tracker.set_value, 1,
            run_time=10,
            rate_func=linear
        )

    def get_input_line(self, rect):
        result = ClarifyInputAndOutput.get_input_line(self, rect)
        result.stretch(0.9, 0)
        result.set_stroke(width=2)
        for sm in result.get_family():
            if isinstance(sm, DecimalNumber):
                sm.stretch(1 / 0.9, 0)
                sm.set_stroke(width=0)
        return result
        
class ComplexFourierSeriesExample(FourierOfTrebleClef):
    CONFIG = {
        "file_name": "EighthNote",
        "run_time": 10,
        "n_vectors": 200,
        "n_cycles": 2,
        "max_circle_stroke_width": 0.75,
        "drawing_height": 5,
        "center_point": DOWN,
        "top_row_center": 3 * UP,
        "top_row_label_y": 2,
        "top_row_x_spacing": 1.75,
        "top_row_copy_scale_factor": 0.9,
        "start_drawn": False,
        "plane_config": {
            "axis_config": {"unit_size": 2},
            "y_min": -1.25,
            "y_max": 1.25,
            "x_min": -2.5,
            "x_max": 2.5,
            "background_line_style": {
                "stroke_width": 1,
                "stroke_color": LIGHT_GREY,
            },
        },
        "top_rect_height": 2.5,
    }

    def construct(self):
        self.add_vectors_circles_path()
        self.add_top_row(self.vectors, self.circles)
        self.write_title()
        self.highlight_vectors_one_by_one()
        self.change_shape()

    def write_title(self):
        title = TextMobject("Complex\\\\Fourier series")
        title.scale(1.5)
        title.to_edge(LEFT)
        title.match_y(self.path)

        self.wait(11)
        self.play(FadeInFromDown(title))
        self.wait(2)
        self.title = title

    def highlight_vectors_one_by_one(self):
        # Don't know why these vectors can't get copied.
        # That seems like a problem that will come up again.
        labels = self.top_row[-1]
        next_anims = []
        for vector, circle, label in zip(self.vectors, self.circles, labels):
            # v_color = vector.get_color()
            c_color = circle.get_color()
            c_stroke_width = circle.get_stroke_width()

            rect = SurroundingRectangle(label, color=PINK)
            self.play(
                # vector.set_color, PINK,
                circle.set_stroke, RED, 3,
                FadeIn(rect),
                *next_anims
            )
            self.wait()
            next_anims = [
                # vector.set_color, v_color,
                circle.set_stroke, c_color, c_stroke_width,
                FadeOut(rect),
            ]
        self.play(*next_anims)

    def change_shape(self):
        # path_mob = TexMobject("\\pi")
        path_mob = SVGMobject("Nail_And_Gear")
        new_path = path_mob.family_members_with_points()[0]
        new_path.set_height(4)
        new_path.move_to(self.path, DOWN)
        new_path.shift(0.5 * UP)

        self.transition_to_alt_path(new_path)
        for n in range(self.n_cycles):
            self.run_one_cycle()

    def transition_to_alt_path(self, new_path, morph_path=False):
        new_coefs = self.get_coefficients_of_path(new_path)
        new_vectors = self.get_rotating_vectors(
            coefficients=new_coefs
        )
        new_drawn_path = self.get_drawn_path(new_vectors)

        self.vector_clock.suspend_updating()

        vectors = self.vectors
        anims = []

        for vect, new_vect in zip(vectors, new_vectors):
            new_vect.update()
            new_vect.clear_updaters()

            line = Line(stroke_width=0)
            line.put_start_and_end_on(*vect.get_start_and_end())
            anims.append(ApplyMethod(
                line.put_start_and_end_on,
                *new_vect.get_start_and_end()
            ))
            vect.freq = new_vect.freq
            vect.coefficient = new_vect.coefficient

            vect.line = line
            vect.add_updater(
                lambda v: v.put_start_and_end_on(
                    *v.line.get_start_and_end()
                )
            )
        if morph_path:
            anims.append(
                ReplacementTransform(
                    self.drawn_path,
                    new_drawn_path
                )
            )
        else:
            anims.append(
                FadeOut(self.drawn_path)
            )

        self.play(*anims, run_time=3)
        for vect in self.vectors:
            vect.remove_updater(vect.updaters[-1])

        if not morph_path:
            self.add(new_drawn_path)
            self.vector_clock.set_value(0)

        self.vector_clock.resume_updating()
        self.drawn_path = new_drawn_path

    #
    def get_path(self):
        path = super().get_path()
        path.set_height(self.drawing_height)
        path.to_edge(DOWN)
        return path

    def add_top_row(self, vectors, circles, max_freq=3):
        self.top_row = self.get_top_row(
            vectors, circles, max_freq
        )
        self.add(self.top_row)

    def get_top_row(self, vectors, circles, max_freq=3):
        vector_copies = VGroup()
        circle_copies = VGroup()
        for vector, circle in zip(vectors, circles):
            if vector.freq > max_freq:
                break
            vcopy = vector.copy()
            vcopy.clear_updaters()
            ccopy = circle.copy()
            ccopy.clear_updaters()
            ccopy.original = circle
            vcopy.original = vector

            vcopy.center_point = op.add(
                self.top_row_center,
                vector.freq * self.top_row_x_spacing * RIGHT,
            )
            ccopy.center_point = vcopy.center_point
            vcopy.add_updater(self.update_top_row_vector_copy)
            ccopy.add_updater(self.update_top_row_circle_copy)
            vector_copies.add(vcopy)
            circle_copies.add(ccopy)

        dots = VGroup(*[
            TexMobject("\\dots").next_to(
                circle_copies, direction,
                MED_LARGE_BUFF,
            )
            for direction in [LEFT, RIGHT]
        ])
        labels = self.get_top_row_labels(vector_copies)
        return VGroup(
            vector_copies,
            circle_copies,
            dots,
            labels,
        )

    def update_top_row_vector_copy(self, vcopy):
        vcopy.become(vcopy.original)
        vcopy.scale(self.top_row_copy_scale_factor)
        vcopy.shift(vcopy.center_point - vcopy.get_start())
        return vcopy

    def update_top_row_circle_copy(self, ccopy):
        ccopy.become(ccopy.original)
        ccopy.scale(self.top_row_copy_scale_factor)
        ccopy.move_to(ccopy.center_point)
        return ccopy

    def get_top_row_labels(self, vector_copies):
        labels = VGroup()
        for vector_copy in vector_copies:
            freq = vector_copy.freq
            label = Integer(freq)
            label.move_to(np.array([
                freq * self.top_row_x_spacing,
                self.top_row_label_y,
                0
            ]))
            labels.add(label)
        return labels

    def setup_plane(self):
        plane = ComplexPlane(**self.plane_config)
        plane.shift(self.center_point)
        plane.add_coordinates()

        top_rect = Rectangle(
            width=FRAME_WIDTH,
            fill_color=BLACK,
            fill_opacity=1,
            stroke_width=0,
            height=self.top_rect_height,
        )
        top_rect.to_edge(UP, buff=0)

        self.plane = plane
        self.add(plane)
        self.add(top_rect)

    def get_path_end(self, vectors, stroke_width=None, **kwargs):
        if stroke_width is None:
            stroke_width = self.drawn_path_st
        full_path = self.get_vector_sum_path(vectors, **kwargs)
        path = VMobject()
        path.set_stroke(
            self.drawn_path_color,
            stroke_width
        )

        def update_path(p):
            alpha = self.get_vector_time() % 1
            p.pointwise_become_partial(
                full_path,
                np.clip(alpha - 0.01, 0, 1),
                np.clip(alpha, 0, 1),
            )
            p.points[-1] = vectors[-1].get_end()

        path.add_updater(update_path)
        return path

    def get_drawn_path_alpha(self):
        return super().get_drawn_path_alpha() - 0.002

    def get_drawn_path(self, vectors, stroke_width=2, **kwargs):
        odp = super().get_drawn_path(vectors, stroke_width, **kwargs)
        return VGroup(
            odp,
            self.get_path_end(vectors, stroke_width, **kwargs),
        )

    def get_vertically_falling_tracing(self, vector, color, stroke_width=3, rate=0.25):
        path = VMobject()
        path.set_stroke(color, stroke_width)
        path.start_new_path(vector.get_end())
        path.vector = vector

        def update_path(p, dt):
            p.shift(rate * dt * DOWN)
            p.add_smooth_curve_to(p.vector.get_end())
        path.add_updater(update_path)
        return path


class PiFourierSeries(ComplexFourierSeriesExample):
    CONFIG = {
        "tex": "\\pi",
        "n_vectors": 101,
        "path_height": 3.5,
        "max_circle_stroke_width": 1,
        "top_row_copy_scale_factor": 0.6,
    }

    def construct(self):
        self.setup_plane()
        self.add_vectors_circles_path()
        self.add_top_row(self.vectors, self.circles)

        for n in range(self.n_cycles):
            self.run_one_cycle()

    def get_path(self):
        pi = TexMobject(self.tex)
        path = pi.family_members_with_points()[0]
        path.set_height(self.path_height)
        path.move_to(3 * DOWN, DOWN)
        path.set_stroke(YELLOW, 0)
        path.set_fill(opacity=0)
        return path


class RealValuedFunctionFourierSeries(PiFourierSeries):
    CONFIG = {
        "n_vectors": 101,
        "start_drawn": True,
    }

    def construct(self):
        self.setup_plane()
        self.add_vectors_circles_path()
        self.add_top_row(self.vectors, self.circles)

        self.flatten_path()
        self.focus_on_vector_pair()

    def flatten_path(self):
        new_path = self.path.copy()
        new_path.stretch(0, 1)
        new_path.set_y(self.plane.n2p(0)[1])
        self.vector_clock.set_value(10)
        self.transition_to_alt_path(new_path, morph_path=True)
        self.run_one_cycle()

    def focus_on_vector_pair(self):
        vectors = self.vectors
        circles = self.circles
        top_row = self.top_row
        top_vectors, top_circles, dots, labels = top_row

        rects1, rects2, rects3 = [
            VGroup(*[
                SurroundingRectangle(VGroup(
                    top_circles[i],
                    labels[i],
                ))
                for i in pair
            ]).set_stroke(LIGHT_GREY, 2)
            for pair in [(1, 2), (3, 4), (5, 6)]
        ]

        def get_opacity_animation(i1, i2, alpha_func):
            v_group = vectors[i1:i2]
            c_group = circles[i1:i2]
            return AnimationGroup(
                UpdateFromAlphaFunc(
                    VectorizedPoint(),
                    lambda m, a: v_group.set_opacity(
                        alpha_func(a)
                    )
                ),
                UpdateFromAlphaFunc(
                    VectorizedPoint(),
                    lambda m, a: c_group.set_stroke(
                        opacity=alpha_func(a)
                    )
                ),
            )

        self.remove(self.path, self.drawn_path)
        self.play(
            get_opacity_animation(
                3, len(vectors), lambda a: smooth(1 - a),
            ),
            ShowCreation(rects1, lag_ratio=0.3),
        )
        traced_path2 = self.get_vertically_falling_tracing(vectors[2], GREEN)
        self.add(traced_path2)
        for n in range(3):
            self.run_one_cycle()

        self.play(
            get_opacity_animation(3, 5, smooth),
            get_opacity_animation(
                0, 3,
                lambda a: 1 - 0.75 * smooth(a)
            ),
            ReplacementTransform(rects1, rects2),
        )
        traced_path2.set_stroke(width=1)
        traced_path4 = self.get_vertically_falling_tracing(vectors[4], YELLOW)
        self.add(traced_path4)
        self.run_one_cycle()
        self.play(
            get_opacity_animation(5, 7, smooth),
            get_opacity_animation(
                3, 5,
                lambda a: 1 - 0.75 * smooth(a)
            ),
            ReplacementTransform(rects2, rects3),
        )
        traced_path2.set_stroke(width=1)
        traced_path4.set_stroke(width=1)
        traced_path6 = self.get_vertically_falling_tracing(vectors[6], TEAL)
        self.add(traced_path6)
        for n in range(2):
            self.run_one_cycle()


class DemonstrateAddingArrows(PiFourierSeries):
    CONFIG = {
        "tex": "\\leftarrow",
        "n_arrows": 21,
        "parametric_function_step_size": 0.1,
    }

    def construct(self):
        self.setup_plane()
        self.add_vectors_circles_path()
        self.add_top_row(self.vectors, self.circles)

        circles = self.circles
        original_vectors = self.vectors
        vectors = VGroup(*[
            Vector(
                **self.vector_config
            ).put_start_and_end_on(*v.get_start_and_end())
            for v in original_vectors
        ])
        original_top_vectors = self.top_row[0]
        top_vectors = VGroup(*[
            Vector(
                **self.vector_config
            ).put_start_and_end_on(*v.get_start_and_end())
            for v in original_top_vectors
        ])

        self.plane.axes.set_stroke(LIGHT_GREY, 1)

        self.vector_clock.suspend_updating()
        self.remove(circles, original_vectors)
        self.remove(self.path, self.drawn_path)
        anims1 = [
            TransformFromCopy(tv, v)
            for tv, v in zip(top_vectors, vectors)
        ]
        anims2 = [
            ShowCreation(v)
            for v in vectors[len(top_vectors):25]
        ]
        self.play(
            LaggedStart(*anims1),
            run_time=3,
            lag_ratio=0.2,
        )
        self.play(
            LaggedStart(*anims2),
            lag_ratio=0.1,
            run_time=5,
        )


class LabelRotatingVectors(PiFourierSeries):
    CONFIG = {
        "n_vectors": 6,
        "center_point": 1.5 * DOWN,
        "top_rect_height": 3,
        "plane_config": {
            "axis_config": {
                "unit_size": 1.75,
                "stroke_color": LIGHT_GREY,
            },
        },
        "top_row_x_spacing": 1.9,
        "top_row_center": 3 * UP + 0.2 * LEFT,
    }

    def construct(self):
        self.setup_plane()
        self.setup_top_row()

        self.ask_about_labels()
        self.initialize_at_one()
        self.show_complex_exponents()
        # self.show_complex_exponents_temp()

        self.tweak_initial_states()
        self.constant_examples()

    def setup_top_row(self):
        vectors = self.get_rotating_vectors(
            coefficients=0.5 * np.ones(self.n_vectors)
        )
        circles = self.get_circles(vectors)

        top_row = self.get_top_row(vectors, circles)
        top_row.shift(0.5 * DOWN + 0.25 * RIGHT)
        v_copies, c_copies, dots, labels = top_row
        labels.to_edge(UP, MED_SMALL_BUFF)
        freq_label = TextMobject("Frequencies:")
        freq_label.to_edge(LEFT, MED_SMALL_BUFF)
        freq_label.match_y(labels)
        VGroup(freq_label, labels).set_color(YELLOW)

        def get_constant_func(const):
            return lambda: const

        for vector, v_copy in zip(vectors, v_copies):
            vector.center_func = get_constant_func(
                v_copy.get_start()
            )
        vectors.update(0)
        circles.update(0)

        self.add(vectors)
        self.add(circles)
        self.add(dots)
        self.add(freq_label)
        self.add(labels)

        self.vectors = vectors
        self.circles = circles
        self.labels = labels
        self.freq_label = freq_label

    def ask_about_labels(self):
        circles = self.circles

        formulas = TextMobject("Formulas:")
        formulas.next_to(circles, DOWN)
        formulas.to_edge(LEFT, MED_SMALL_BUFF)

        q_marks = VGroup(*[
            TexMobject("??").scale(1.0).next_to(circle, DOWN)
            for circle in circles
        ])

        self.play(FadeInFrom(formulas, DOWN))
        self.play(LaggedStartMap(
            FadeInFrom, q_marks,
            lambda m: (m, UP),
            lag_ratio=0.2,
            run_time=3,
        ))
        self.wait(3)

        self.q_marks = q_marks
        self.formulas_word = formulas

    def initialize_at_one(self):
        vectors = self.vectors
        circles = self.circles
        vector_clock = self.vector_clock
        plane = self.plane
        q_marks = self.q_marks

        # Why so nuclear?
        vc_updater = vector_clock.updaters.pop()
        self.play(
            vector_clock.set_value, 0,
            run_time=2,
        )

        zero_vect = Vector()
        zero_vect.replace(vectors[0])
        zero_circle = self.get_circle(zero_vect)
        zero_circle.match_style(circles[0])
        self.add(zero_circle)

        one_label = TexMobject("1")
        one_label.move_to(q_marks[0])

        self.play(
            zero_vect.put_start_and_end_on,
            plane.n2p(0), plane.n2p(1),
        )
        vector_clock.add_updater(vc_updater)
        self.wait()
        self.play(
            FadeOutAndShift(q_marks[0], UP),
            FadeInFrom(one_label, DOWN),
        )
        self.wait(4)

        self.one_label = one_label
        self.zero_vect = zero_vect
        self.zero_circle = zero_circle

    def show_complex_exponents(self):
        vectors = self.vectors
        circles = self.circles
        q_marks = self.q_marks
        labels = self.labels
        one_label = self.one_label
        v_lines = self.get_v_lines(circles)

        # Vector 1
        v1_rect = SurroundingRectangle(
            VGroup(circles[1], q_marks[1], labels[1]),
            stroke_color=GREY,
            stroke_width=2,
        )
        f1_exp = self.get_exp_tex()
        f1_exp.move_to(q_marks[1], DOWN)

        self.play(
            FadeOut(self.zero_vect),
            FadeOut(self.zero_circle),
            FadeIn(v1_rect)
        )

        vg1 = self.get_vector_in_plane_group(
            vectors[1], circles[1],
        )
        vg1_copy = vg1.copy()
        vg1_copy.clear_updaters()
        vg1_copy.replace(circles[1])

        cps_1 = self.get_cps_label(1)

        circle_copy = vg1[1].copy().clear_updaters()
        circle_copy.set_stroke(YELLOW, 3)
        arclen_decimal = DecimalNumber(
            num_decimal_places=3,
            show_ellipsis=True,
        )
        arclen_tracker = ValueTracker(0)
        arclen_decimal.add_updater(lambda m: m.next_to(
            circle_copy.get_end(), UR, SMALL_BUFF,
        ))
        arclen_decimal.add_updater(lambda m: m.set_value(
            arclen_tracker.get_value()
        ))

        self.play(
            ReplacementTransform(vg1_copy, vg1),
        )
        self.play(FadeInFrom(cps_1, DOWN))
        self.wait(2)
        self.play(
            FadeOutAndShift(q_marks[1], UP),
            FadeInFrom(f1_exp, DOWN),
        )
        self.wait(2)
        self.play(ShowCreationThenFadeAround(
            f1_exp.get_part_by_tex("2\\pi")
        ))
        self.add(arclen_decimal),
        self.play(
            ShowCreation(circle_copy),
            arclen_tracker.set_value, TAU,
            run_time=3,
        )
        self.wait()
        self.play(
            FadeOut(circle_copy),
            FadeOut(arclen_decimal),
        )
        self.wait(8)
        self.play(
            v1_rect.move_to, circles[2],
            v1_rect.match_y, v1_rect,
            FadeOut(vg1),
            FadeOut(cps_1),
        )

        # Vector -1
        vgm1 = self.get_vector_in_plane_group(
            vectors[2], circles[2],
        )
        vgm1_copy = vgm1.copy()
        vgm1_copy.clear_updaters()
        vgm1_copy.replace(circles[2])
        cps_m1 = self.get_cps_label(-1)
        fm1_exp = self.get_exp_tex(-1)
        fm1_exp.move_to(q_marks[2], DOWN)

        self.play(
            ReplacementTransform(vgm1_copy, vgm1),
            FadeInFromDown(cps_m1)
        )
        self.wait(2)
        self.play(
            FadeOutAndShift(q_marks[2], UP),
            FadeInFromDown(fm1_exp),
            v1_rect.stretch, 1.4, 0,
        )
        self.wait(5)
        self.play(
            v1_rect.move_to, circles[3],
            v1_rect.match_y, v1_rect,
            FadeOut(vgm1),
            FadeOut(cps_m1),
        )

        # Vector 2
        # (Lots of copy-pasting here)
        vg2 = self.get_vector_in_plane_group(
            vectors[3], circles[3],
        )
        vg2_copy = vg2.copy()
        vg2_copy.clear_updaters()
        vg2_copy.replace(circles[3])
        cps_2 = self.get_cps_label(2)
        f2_exp = self.get_exp_tex(2)
        f2_exp.move_to(q_marks[3], DOWN)
        circle_copy.append_vectorized_mobject(circle_copy)

        self.play(
            ReplacementTransform(vg2_copy, vg2),
            FadeInFromDown(cps_2)
        )
        self.wait()
        self.play(
            FadeOutAndShift(q_marks[3], UP),
            FadeInFromDown(f2_exp),
        )
        self.wait(3)

        self.play(ShowCreationThenFadeAround(
            f2_exp.get_parts_by_tex("2"),
        ))
        self.add(arclen_decimal)
        arclen_tracker.set_value(0)
        self.play(
            ShowCreation(circle_copy),
            arclen_tracker.set_value, 2 * TAU,
            run_time=5
        )
        self.wait(3)
        self.play(
            FadeOut(circle_copy),
            FadeOut(arclen_decimal),
        )
        self.play(
            FadeOut(vg2),
            FadeOut(cps_2),
            FadeOut(v1_rect),
        )

        # Show all formulas
        fm2_exp = self.get_exp_tex(-2)
        fm2_exp.move_to(q_marks[4], DOWN)
        f3_exp = self.get_exp_tex(3)
        f3_exp.move_to(q_marks[5], DOWN)
        f1_exp_new = self.get_exp_tex(1)
        f1_exp_new.move_to(q_marks[1], DOWN)
        f0_exp = self.get_exp_tex(0)
        f0_exp.move_to(q_marks[0], DOWN)
        f_exp_general = self.get_exp_tex("n")
        f_exp_general.next_to(self.formulas_word, DOWN)

        self.play(
            FadeOut(q_marks[4:]),
            FadeOut(f1_exp),
            FadeIn(f1_exp_new),
            FadeInFromDown(fm2_exp),
            FadeInFromDown(f3_exp),
            FadeIn(v_lines, lag_ratio=0.2)
        )
        self.play(
            FadeInFrom(f_exp_general, UP)
        )
        self.play(ShowCreationThenFadeAround(f_exp_general))
        self.wait(3)
        self.play(
            FadeOut(one_label, UP),
            TransformFromCopy(f_exp_general, f0_exp),
        )
        self.wait(5)

        self.f_exp_labels = VGroup(
            f0_exp, f1_exp_new, fm1_exp,
            f2_exp, fm2_exp, f3_exp,
        )
        self.f_exp_general = f_exp_general

    def show_complex_exponents_temp(self):
        self.f_exp_labels = VGroup(*[
            self.get_exp_tex(n).move_to(qm, DOWN)
            for n, qm in zip(
                [0, 1, -1, 2, -2, 3],
                self.q_marks,
            )
        ])
        self.f_exp_general = self.get_exp_tex("n")
        self.f_exp_general.next_to(self.formulas_word, DOWN)

        self.remove(*self.q_marks, self.one_label)
        self.remove(self.zero_vect, self.zero_circle)
        self.add(self.f_exp_labels, self.f_exp_general)

    def tweak_initial_states(self):
        vector_clock = self.vector_clock
        f_exp_labels = self.f_exp_labels
        f_exp_general = self.f_exp_general
        vectors = self.vectors

        cn_terms = VGroup()
        for i, f_exp in enumerate(f_exp_labels):
            n = (i + 1) // 2
            if i % 2 == 0 and i > 0:
                n *= -1
            cn_terms.add(self.get_cn_label(n, f_exp))
        cn_general = self.get_cn_label("n", f_exp_general)

        new_coefs = [
            0.5,
            np.exp(complex(0, TAU / 8)),
            0.7 * np.exp(-complex(0, TAU / 8)),
            0.6 * np.exp(complex(0, TAU / 3)),
            1.1 * np.exp(-complex(0, TAU / 12)),
            0.3 * np.exp(complex(0, TAU / 12)),
        ]

        def update_vectors(alpha):
            for vect, new_coef in zip(vectors, new_coefs):
                vect.coefficient = 0.5 * interpolate(
                    1, new_coef, alpha
                )

        vector_clock.incrementer = vector_clock.updaters.pop()
        self.play(
            vector_clock.set_value,
            int(vector_clock.get_value())
        )
        self.play(
            LaggedStartMap(
                MoveToTarget,
                VGroup(f_exp_general, *f_exp_labels),
            ),
            LaggedStartMap(
                FadeInFromDown,
                VGroup(cn_general, *cn_terms),
            ),
            UpdateFromAlphaFunc(
                VectorizedPoint(),
                lambda m, a: update_vectors(a)
            ),
            run_time=2
        )
        self.wait()
        self.play(
            LaggedStart(*[
                ShowCreationThenFadeAround(
                    cn_term,
                    surrounding_rectangle_config={
                        "buff": 0.05,
                        "stroke_width": 2,
                    },
                )
                for cn_term in cn_terms
            ])
        )

        self.cn_terms = cn_terms
        self.cn_general = cn_general

    def constant_examples(self):
        cn_terms = self.cn_terms
        vectors = self.vectors
        circles = self.circles

        # c0 term
        c0_brace = Brace(cn_terms[0], DOWN, buff=SMALL_BUFF)
        c0_label = TexMobject("0.5")
        c0_label.next_to(c0_brace, DOWN, SMALL_BUFF)
        c0_label.add_background_rectangle()
        vip_group0 = self.get_vector_in_plane_group(
            vectors[0], circles[0]
        )
        vip_group0_copy = vip_group0.copy()
        vip_group0_copy.clear_updaters()
        vip_group0_copy.replace(circles[0])

        self.play(
            Transform(vip_group0_copy, vip_group0)
        )
        self.wait()
        self.play(vip_group0_copy.scale, 2)
        self.play(
            vip_group0_copy.scale, 0.5,
            GrowFromCenter(c0_brace),
            GrowFromCenter(c0_label),
        )
        self.wait(2)
        self.play(
            FadeOut(c0_brace),
            FadeOut(c0_label),
            FadeOut(vip_group0_copy),
        )

        # c1 term
        c1_brace = Brace(cn_terms[1], DOWN, buff=SMALL_BUFF)
        c1_label = TexMobject("e^{(\\pi / 4)i}")
        c1_label.next_to(c1_brace, DOWN, SMALL_BUFF)
        c1_decimal = DecimalNumber(
            np.exp(np.complex(0, PI / 4)),
            num_decimal_places=3,
        )
        approx = TexMobject("\\approx")
        approx.next_to(c1_label, RIGHT, MED_SMALL_BUFF)
        c1_decimal.next_to(approx, RIGHT, MED_SMALL_BUFF)
        scalar = DecimalNumber(0.3)
        scalar.next_to(
            c1_label, LEFT, SMALL_BUFF,
            aligned_edge=DOWN,
        )

        vip_group1 = self.get_vector_in_plane_group(
            vectors[1], circles[1]
        )
        vip_group1_copy = vip_group1.copy()
        vip_group1_copy[0].stroke_width = 3
        vip_group1_copy.clear_updaters()
        vip_group1_copy.save_state()
        vip_group1_copy.replace(circles[1])

        self.play(
            Restore(vip_group1_copy)
        )
        self.play(Rotate(vip_group1_copy, -PI / 4))
        self.play(Rotate(vip_group1_copy, PI / 4))
        self.play(
            GrowFromCenter(c1_brace),
            FadeIn(c1_label),
        )
        self.play(
            Write(approx),
            Write(c1_decimal),
            run_time=1,
        )
        self.wait(2)

        def update_v1(alpha):
            vectors[1].coefficient = 0.5 * interpolate(
                np.exp(complex(0, PI / 4)),
                0.3 * np.exp(complex(0, PI / 4)),
                alpha
            )

        self.play(
            FadeIn(scalar),
            c1_decimal.set_value,
            scalar.get_value() * c1_decimal.get_value(),
            vip_group1_copy.scale, scalar.get_value(),
            UpdateFromAlphaFunc(
                VMobject(),
                lambda m, a: update_v1(a)
            )
        )
        self.wait()
        self.play(
            FadeOut(c1_brace),
            FadeOut(c1_label),
            FadeOut(approx),
            FadeOut(c1_decimal),
            FadeOut(scalar),
            FadeOut(vip_group1_copy),
        )

        fade_anims = []
        for cn_term, vect in zip(cn_terms[2:], vectors[2:]):
            rect = SurroundingRectangle(cn_term, buff=0.025)
            rect.set_stroke(width=2)
            decimal = DecimalNumber(vect.coefficient)
            decimal.next_to(rect, DOWN)
            decimal.add_background_rectangle()
            if cn_term is cn_terms[4]:
                decimal.shift(0.7 * RIGHT)

            self.play(
                ShowCreation(rect),
                FadeIn(decimal),
                *fade_anims
            )
            self.wait()
            fade_anims = [FadeOut(rect), FadeOut(decimal)]
        self.play(*fade_anims)

    #
    def get_vector_in_plane_group(self, top_vector, top_circle):
        plane = self.plane
        origin = plane.n2p(0)

        vector = Vector()
        vector.add_updater(
            lambda v: v.put_start_and_end_on(
                origin,
                plane.n2p(2 * top_vector.coefficient)
            ).set_angle(top_vector.get_angle())
        )
        circle = Circle()
        circle.match_style(top_circle)
        circle.set_width(2 * vector.get_length())
        circle.move_to(origin)

        return VGroup(vector, circle)

    def get_exp_tex(self, freq=None):
        if freq is None:
            freq_str = "{}"
        else:
            freq_str = "{" + str(freq) + "}" + "\\cdot"

        result = TexMobject(
            "e^{", freq_str, "2\\pi i {t}}",
            tex_to_color_map={
                "2\\pi": WHITE,
                "{t}": PINK,
                freq_str: YELLOW,
            }
        )
        result.scale(0.9)
        return result

    def get_cn_label(self, n, exp_label):
        exp_label.generate_target()
        exp_label.target.scale(0.9)

        n_str = "{" + str(n) + "}"
        term = TexMobject("c_", n_str)
        term.set_color(GREEN)
        term[1].set_color(YELLOW)
        term[1].set_width(0.12)
        term[1].move_to(term[0].get_corner(DR), LEFT)
        if isinstance(n, str):
            term[1].scale(1.4, about_edge=LEFT)
            term[1].shift(0.03 * RIGHT)
        elif n < 0:
            term[1].scale(1.4, about_edge=LEFT)
            term[1].set_stroke(width=0.5)
        else:
            term[1].shift(0.05 * RIGHT)
        term.scale(0.9)
        term.shift(
            exp_label.target[0].get_corner(LEFT) -
            term[0].get_corner(RIGHT) +
            0.2 * LEFT
        )
        VGroup(exp_label.target, term).move_to(
            exp_label, DOWN
        )

        if isinstance(n, str):
            VGroup(term, exp_label.target).scale(
                1.3, about_edge=UP
            )

        return term

    def get_cps_label(self, n):
        n_str = str(n)
        if n == 1:
            frac_tex = "\\frac{\\text{cycle}}{\\text{second}}"
        else:
            frac_tex = "\\frac{\\text{cycles}}{\\text{second}}"

        result = TexMobject(
            n_str, frac_tex,
            tex_to_color_map={
                n_str: YELLOW
            },
        )
        result[1].scale(0.7, about_edge=LEFT)
        result[0].scale(1.2, about_edge=RIGHT)
        result.next_to(self.plane.n2p(2), UR)
        return result

    def get_v_lines(self, circles):
        lines = VGroup()
        o_circles = VGroup(*circles)
        o_circles.sort(lambda p: p[0])
        for c1, c2 in zip(o_circles, o_circles[1:]):
            line = DashedLine(3 * UP, ORIGIN)
            line.set_stroke(WHITE, 1)
            line.move_to(midpoint(
                c1.get_center(), c2.get_center(),
            ))
            lines.add(line)
        return lines


class IntegralTrick(LabelRotatingVectors, TRangingFrom0To1):
    CONFIG = {
        "file_name": "EighthNote",
        "n_vectors": 101,
        "path_height": 3.5,
        "plane_config": {
            "x_min": -1.75,
            "x_max": 1.75,
            "axis_config": {
                "unit_size": 1.75,
                "stroke_color": LIGHT_GREY,
            },
        },
        "center_point": 1.5 * DOWN + 3 * RIGHT,
        "input_space_rect_config": {
            "width": 6,
            "height": 1.5,
        },
        "start_drawn": True,
        "parametric_function_step_size": 0.01,
        "top_row_center": 2 * UP + RIGHT,
        "top_row_x_spacing": 2.25,
    }

    def construct(self):
        self.setup_plane()
        self.add_vectors_circles_path()
        self.setup_input_space()
        self.setup_input_trackers()
        self.setup_top_row()
        self.setup_sum()

        self.introduce_sum()
        self.issolate_c0()
        self.show_center_of_mass()
        self.write_integral()

    def setup_input_space(self):
        super().setup_input_space()
        self.input_line.next_to(
            self.input_rect.get_bottom(),
            UP,
        )
        group = VGroup(
            self.input_rect,
            self.input_line,
        )
        group.move_to(self.plane.n2p(0))
        group.to_edge(LEFT)

    def setup_top_row(self):
        top_row = self.get_top_row(
            self.vectors, self.circles,
            max_freq=2,
        )
        self.top_vectors, self.top_circles, dots, labels = top_row

        self.add(*top_row)
        self.remove(labels)

    def setup_sum(self):
        top_vectors = self.top_vectors

        terms = VGroup()
        for vect in top_vectors:
            freq = vect.freq
            exp = self.get_exp_tex(freq)
            cn = self.get_cn_label(freq, exp)
            exp.become(exp.target)
            term = VGroup(cn, exp)
            term.move_to(vect.get_start())
            term.shift(UP)
            terms.add(term)

        for vect in [LEFT, RIGHT]:
            dots = TexMobject("\\cdots")
            dots.next_to(terms, vect, MED_LARGE_BUFF)
            terms.add(dots)

        plusses = VGroup()
        o_terms = VGroup(*terms)
        o_terms.sort(lambda p: p[0])
        for t1, t2 in zip(o_terms, o_terms[1:]):
            plus = TexMobject("+")
            plus.scale(0.7)
            plus.move_to(midpoint(
                t1.get_right(),
                t2.get_left(),
            ))
            plusses.add(plus)
        terms[:-2].shift(0.05 * UP)

        ft_eq = TexMobject("f(t)", "= ")
        ft_eq.next_to(terms, LEFT)

        self.add(terms)
        self.add(plusses)
        self.add(ft_eq)

        self.terms = terms
        self.plusses = plusses
        self.ft_eq = ft_eq

    def introduce_sum(self):
        self.remove(
            self.vector_clock,
            self.vectors,
            self.circles,
            self.drawn_path,
        )

        ft = self.ft_eq[0]
        terms = self.terms
        path = self.path
        input_tracker = self.input_tracker

        rect = SurroundingRectangle(ft)
        coefs = VGroup(*[term[0] for term in terms[:-2]])
        terms_rect = SurroundingRectangle(terms)
        terms_rect.set_stroke(YELLOW, 1.5)

        dot = Dot()
        dot.add_updater(lambda d: d.move_to(path.get_end()))

        self.play(ShowCreation(rect))
        self.wait()
        self.play(
            ReplacementTransform(rect, dot)
        )
        path.set_stroke(YELLOW, 2)
        self.play(
            ShowCreation(path),
            input_tracker.set_value, 1,
            run_time=3,
            rate_func=lambda t: smooth(t, 1),
        )
        self.wait()

        input_tracker.add_updater(
            lambda m: m.set_value(
                self.vector_clock.get_value() % 1
            )
        )
        self.add(
            self.vector_clock,
            self.vectors,
            self.circles,
        )
        self.play(
            FadeOut(path),
            FadeOut(dot),
            FadeIn(self.drawn_path),
        )
        self.play(FadeIn(terms_rect))
        self.wait()
        self.play(FadeOut(terms_rect))

        fade_outs = []
        for coef in coefs:
            rect = SurroundingRectangle(coef)
            self.play(FadeIn(rect), *fade_outs)
            fade_outs = [FadeOut(rect)]
        self.play(*fade_outs)
        self.wait(2)

        self.vector_clock.clear_updaters()

    def issolate_c0(self):
        vectors = self.vectors
        circles = self.circles
        terms = self.terms
        top_circles = self.top_circles
        path = self.path

        path.set_stroke(YELLOW, 1)

        c0_rect = SurroundingRectangle(
            VGroup(top_circles[0], terms[0])
        )
        c0_rect.set_stroke(WHITE, 1)

        opacity_tracker = ValueTracker(1)
        for vect in vectors[1:]:
            vect.add_updater(
                lambda v: v.set_opacity(
                    opacity_tracker.get_value()
                )
            )
        for circle in circles[0:]:
            circle.add_updater(
                lambda c: c.set_stroke(
                    opacity=opacity_tracker.get_value()
                )
            )

        self.play(ShowCreation(c0_rect))
        self.play(
            opacity_tracker.set_value, 0.2,
            FadeOut(self.drawn_path),
            FadeIn(path)
        )

        v0 = vectors[0]
        v0_point = VectorizedPoint(v0.get_end())
        origin = self.plane.n2p(0)
        v0.add_updater(lambda v: v.put_start_and_end_on(
            origin, v0_point.get_location(),
        ))

        self.play(
            MaintainPositionRelativeTo(path, v0_point),
            ApplyMethod(
                v0_point.shift, 1.5 * LEFT,
                run_time=4,
                rate_func=there_and_back,
                path_arc=60 * DEGREES,
            )
        )
        v0.updaters.pop()

        self.opacity_tracker = opacity_tracker

    def show_center_of_mass(self):
        dot_sets = VGroup(*[
            self.get_sample_dots(dt=dt, radius=radius)
            for dt, radius in [
                (0.05, 0.04),
                (0.01, 0.03),
                (0.0025, 0.02),
            ]
        ])
        input_dots, output_dots = dot_sets[0]
        v0_dot = input_dots[0].deepcopy()
        v0_dot.move_to(center_of_mass([
            od.get_center()
            for od in output_dots
        ]))
        v0_dot.set_color(RED)

        self.play(LaggedStartMap(
            FadeInFromLarge, input_dots,
            lambda m: (m, 5),
            run_time=2,
            lag_ratio=0.5,
        ))
        self.wait()
        self.play(
            TransformFromCopy(
                input_dots,
                output_dots,
                run_time=3
            )
        )
        self.wait()
        self.play(*[
            Transform(
                od.copy(), v0_dot.copy(),
                remover=True
            )
            for od in output_dots
        ])
        self.add(v0_dot)
        self.wait()

        for ds1, ds2 in zip(dot_sets, dot_sets[1:]):
            ind1, outd1 = ds1
            ind2, outd2 = ds2
            new_v0_dot = v0_dot.copy()
            new_v0_dot.move_to(center_of_mass([
                od.get_center()
                for od in outd2
            ]))
            self.play(
                FadeOut(ind1),
                LaggedStartMap(
                    FadeInFrom, ind2,
                    lambda m: (m, UP),
                    lag_ratio=4 / len(ind2),
                    run_time=2,
                )
            )
            self.play(
                TransformFromCopy(ind2, outd2),
                FadeOut(outd1),
                run_time=2,
            )
            self.play(
                FadeOut(v0_dot),
                *[
                    Transform(
                        od.copy(), v0_dot.copy(),
                        remover=True
                    )
                    for od in outd2
                ]
            )
            v0_dot = new_v0_dot
            self.add(v0_dot)
        self.wait()

        self.input_dots, self.output_dots = dot_sets[-1]
        self.v0_dot = v0_dot

    def write_integral(self):
        t_tracker = self.vector_clock
        path = self.path

        expression = TexMobject(
            "c_{0}", "="
            "\\int_0^1 f({t}) d{t}",
            tex_to_color_map={
                "{t}": PINK,
                "{0}": YELLOW,
            },
        )
        expression.next_to(self.input_rect, UP)
        brace = Brace(expression[2:], UP, buff=SMALL_BUFF)
        average = brace.get_text("Average", buff=SMALL_BUFF)

        self.play(
            FadeInFromDown(expression),
            GrowFromCenter(brace),
            FadeIn(average),
        )
        t_tracker.clear_updaters()
        t_tracker.set_value(0)
        self.add(path)
        self.play(
            t_tracker.set_value, 0.999,
            ShowCreation(path),
            run_time=8,
            rate_func=lambda t: smooth(t, 1),
        )
        self.wait()

    #
    def get_path(self):
        mob = SVGMobject(self.file_name)
        path = mob.family_members_with_points()[0]
        path.set_height(self.path_height)
        path.move_to(self.center_point)
        path.shift(0.5 * UR)
        path.set_stroke(YELLOW, 0)
        path.set_fill(opacity=0)
        return path

    def get_sample_dots(self, dt, radius):
        input_line = self.input_line
        path = self.path

        t_values = np.arange(0, 1 + dt, dt)
        dot = Dot(color=PINK, radius=radius)
        dot.set_stroke(
            RED, 1,
            opacity=0.8,
            background=True,
        )
        input_dots = VGroup()
        output_dots = VGroup()
        for t in t_values:
            in_dot = dot.copy()
            out_dot = dot.copy()
            in_dot.move_to(input_line.n2p(t))
            out_dot.move_to(path.point_from_proportion(t))
            input_dots.add(in_dot)
            output_dots.add(out_dot)
        return VGroup(input_dots, output_dots)


class IncreaseOrderOfApproximation(ComplexFourierSeriesExample):
    CONFIG = {
        "file_name": "FourierOneLine",
        "drawing_height": 6,
        "n_vectors": 250,
        "parametric_function_step_size": 0.001,
        "run_time": 10,
        # "n_vectors": 25,
        # "parametric_function_step_size": 0.01,
        # "run_time": 5,
        "slow_factor": 0.05,
    }

    def construct(self):
        path = self.get_path()
        path.to_edge(DOWN)
        path.set_stroke(YELLOW, 2)
        freqs = self.get_freqs()
        coefs = self.get_coefficients_of_path(
            path, freqs=freqs,
        )
        vectors = self.get_rotating_vectors(freqs, coefs)
        circles = self.get_circles(vectors)

        n_tracker = ValueTracker(2)
        n_label = VGroup(
            TextMobject("Approximation using"),
            Integer(100).set_color(YELLOW),
            TextMobject("vectors")
        )
        n_label.arrange(RIGHT)
        n_label.to_corner(UL)
        n_label.add_updater(
            lambda n: n[1].set_value(
                n_tracker.get_value()
            ).align_to(n[2], DOWN)
        )

        changing_path = VMobject()
        vector_copies = VGroup()
        circle_copies = VGroup()

        def update_changing_path(cp):
            n = n_label[1].get_value()
            cp.become(self.get_vector_sum_path(vectors[:n]))
            cp.set_stroke(YELLOW, 2)
            # While we're at it...
            vector_copies.submobjects = list(vectors[:n])
            circle_copies.submobjects = list(circles[:n])

        changing_path.add_updater(update_changing_path)

        self.add(n_label, n_tracker, changing_path)
        self.add(vector_copies, circle_copies)
        self.play(
            n_tracker.set_value, self.n_vectors,
            rate_func=smooth,
            run_time=self.run_time,
        )
        self.wait(5)


class ShowStepFunctionIn2dView(SimpleComplexExponentExample, ComplexFourierSeriesExample):
    CONFIG = {
        "input_space_rect_config": {
            "width": 5,
            "height": 2,
        },
        "input_line_config": {
            "unit_size": 3,
            "x_min": 0,
            "x_max": 1,
            "tick_frequency": 0.1,
            "stroke_width": 2,
            "decimal_number_config": {
                "num_decimal_places": 1,
            }
        },
        "input_numbers": [0, 0.5, 1],
        "input_tex_args": [],
        # "n_vectors": 300,
        "n_vectors": 2,
    }

    def construct(self):
        self.setup_plane()
        self.setup_input_space()
        self.setup_input_trackers()
        self.clear()

        self.transition_from_step_function()
        self.show_output()
        self.show_fourier_series()

    def setup_input_space(self):
        super().setup_input_space()
        rect = self.input_rect
        line = self.input_line
        # rect.stretch(1.2, 1, about_edge=UP)
        line.shift(MED_SMALL_BUFF * UP)
        sf = 1.2
        line.stretch(sf, 0)
        for n in line.numbers:
            n.stretch(1 / sf, 0)

        label = TextMobject("Input space")
        label.next_to(rect.get_bottom(), UP, SMALL_BUFF)
        self.add(label)
        self.input_space_label = label

    def transition_from_step_function(self):
        x_axis = self.input_line
        input_tip = self.input_tip
        input_label = self.input_label
        input_rect = self.input_rect
        input_space_label = self.input_space_label
        plane = self.plane
        plane.set_opacity(0)

        x_axis.save_state()
        # x_axis.center()
        x_axis.move_to(ORIGIN, LEFT)
        sf = 1.5
        x_axis.stretch(sf, 0)
        for number in x_axis.numbers:
            number.stretch(1 / sf, 0)
        x_axis.numbers[0].set_opacity(0)

        y_axis = NumberLine(
            unit_size=2,
            x_min=-1.5,
            x_max=1.5,
            tick_frequency=0.5,
            stroke_color=LIGHT_GREY,
            stroke_width=2,
        )
        # y_axis.match_style(x_axis)
        y_axis.rotate(90 * DEGREES)
        y_axis.shift(x_axis.n2p(0) - y_axis.n2p(0))
        y_axis.add_numbers(
            -1, 0, 1,
            direction=LEFT,
        )
        axes = Axes()
        axes.x_axis = x_axis
        axes.y_axis = y_axis
        axes.axes = VGroup(x_axis, y_axis)

        graph = VGroup(
            Line(
                axes.c2p(0, 1),
                axes.c2p(0.5, 1),
                color=RED,
            ),
            Line(
                axes.c2p(0.5, -1),
                axes.c2p(1, -1),
                color=BLUE,
            ),
        )

        dot1 = Dot(color=RED)
        dot2 = Dot(color=BLUE)
        dot1.add_updater(lambda d: d.move_to(y_axis.n2p(1)))
        dot2.add_updater(lambda d: d.move_to(y_axis.n2p(-1)))
        squish_graph = VGroup(dot1, dot2)

        self.add(x_axis)
        self.add(y_axis)
        self.add(input_tip)
        self.add(input_label)

        self.play(
            self.input_tracker.set_value, 1,
            ShowCreation(graph),
            run_time=3,
            rate_func=lambda t: smooth(t, 1)
        )
        self.wait()
        self.add(
            plane, input_rect, input_space_label,
            x_axis, input_tip, input_label,
        )
        self.play(
            FadeIn(input_rect),
            FadeIn(input_space_label),
            Restore(x_axis),
        )
        self.play(ReplacementTransform(graph, squish_graph))

        # Rotate y-axis, fade in plane
        y_axis.generate_target(use_deepcopy=True)
        y_axis.target.rotate(-TAU / 4)
        y_axis.target.shift(
            plane.n2p(0) - y_axis.target.n2p(0)
        )
        y_axis.target.numbers.set_opacity(0)

        plane.set_opacity(1)
        self.play(
            MoveToTarget(y_axis),
            ShowCreation(plane),
        )
        self.play(FadeOut(y_axis))
        self.wait()
        self.play(self.input_tracker.set_value, 0)

        self.output_dots = squish_graph

    def show_output(self):
        input_tracker = self.input_tracker

        def get_output_point():
            return self.get_output_point(input_tracker.get_value())

        tip = ArrowTip(start_angle=-TAU / 4)
        tip.set_fill(YELLOW)
        tip.match_height(self.input_tip)
        tip.add_updater(lambda m: m.move_to(
            get_output_point(), DOWN,
        ))
        output_label = TextMobject("Output")
        output_label.add_background_rectangle()
        output_label.add_updater(lambda m: m.next_to(
            tip, UP, SMALL_BUFF,
        ))

        self.play(
            FadeIn(tip),
            FadeIn(output_label),
        )

        self.play(
            input_tracker.set_value, 1,
            run_time=8,
            rate_func=linear
        )
        self.wait()
        self.play(input_tracker.set_value, 0)

        self.output_tip = tip

    def show_fourier_series(self):
        plane = self.plane
        input_tracker = self.input_tracker
        output_tip = self.output_tip

        self.play(
            plane.axes.set_stroke, WHITE, 1,
            plane.background_lines.set_stroke, LIGHT_GREY, 0.5,
            plane.faded_lines.set_stroke, LIGHT_GREY, 0.25, 0.5,
        )

        self.vector_clock.set_value(0)
        self.add(self.vector_clock)
        input_tracker.add_updater(lambda m: m.set_value(
            self.vector_clock.get_value() % 1
        ))
        self.add_vectors_circles_path()
        self.remove(self.drawn_path)
        self.add(self.vectors)
        output_tip.clear_updaters()
        output_tip.add_updater(lambda m: m.move_to(
            self.vectors[-1].get_end(), DOWN
        ))

        self.run_one_cycle()
        path = self.get_vertically_falling_tracing(
            self.vectors[1], GREEN, rate=0.5,
        )
        self.add(path)
        for x in range(3):
            self.run_one_cycle()

    #
    def get_freqs(self):
        n = self.n_vectors
        all_freqs = [
            *range(1, n + 1 // 2, 2),
            *range(-1, -n + 1 // 2, -2),
        ]
        all_freqs.sort(key=abs)
        return all_freqs

    def get_path(self):
        path = VMobject()
        p0, p1 = [
            self.get_output_point(x)
            for x in [0, 1]
        ]
        for p in p0, p1:
            path.start_new_path(p)
            path.add_line_to(p)
        return path

    def get_output_point(self, x):
        return self.plane.n2p(self.step(x))

    def step(self, x):
        if x < 0.5:
            return 1
        elif x == 0.5:
            return 0
        else:
            return -1


class AddVectorsOneByOne(IntegralTrick):
    CONFIG = {
        "file_name": "TrebleClef",
        # "start_drawn": True,
        "n_vectors": 101,
        "path_height": 5,
    }

    def construct(self):
        self.setup_plane()
        self.add_vectors_circles_path()
        self.setup_input_space()
        self.setup_input_trackers()
        self.setup_top_row()
        self.setup_sum()

        self.show_sum()

    def show_sum(self):
        vectors = self.vectors
        vector_clock = self.vector_clock
        terms = self.terms

        vector_clock.suspend_updating()
        coef_tracker = ValueTracker(0)

        def update_vector(vector):
            vector.coefficient = interpolate(
                1, vector.original_coefficient,
                coef_tracker.get_value()
            )

        for vector in vectors:
            vector.original_coefficient = vector.coefficient
            vector.add_updater(update_vector)

        rects = VGroup(*[
            SurroundingRectangle(t[0])
            for t in terms[:5]
        ])

        self.remove(self.drawn_path)
        self.play(LaggedStartMap(
            VFadeInThenOut, rects
        ))
        self.play(
            coef_tracker.set_value, 1,
            run_time=3
        )
        self.wait()
        vector_clock.resume_updating()
        self.input_tracker.add_updater(
            lambda m: m.set_value(vector_clock.get_value() % 1)
        )
        self.add(self.drawn_path, self.input_tracker)
        self.wait(10)

    def get_path(self):
        mob = SVGMobject(self.file_name)
        path = mob.family_members_with_points()[0]
        path.set_height(self.path_height)
        path.move_to(self.plane.n2p(0))
        path.set_stroke(YELLOW, 0)
        path.set_fill(opacity=0)
        return path


class DE4Thumbnail(ComplexFourierSeriesExample):
    CONFIG = {
        "file_name": "FourierOneLine",
        "start_drawn": True,
        "n_vectors": 300,
        "parametric_function_step_size": 0.0025,
        "drawn_path_stroke_width": 7,
        "drawing_height": 6,
    }

    def construct(self):
        name = TextMobject("Fourier series")
        name.set_width(FRAME_WIDTH - 2)
        name.to_edge(UP)
        name.set_color(YELLOW)
        subname = TextMobject("a.k.a ``everything is rotations''")
        subname.match_width(name)
        subname.next_to(name, DOWN)
        VGroup(name, subname).to_edge(DOWN)

        self.add(name)
        self.add(subname)

        path = self.get_path()
        path.to_edge(DOWN)
        path.set_stroke(YELLOW, 2)
        freqs = self.get_freqs()
        coefs = self.get_coefficients_of_path(path, freqs=freqs)
        vectors = self.get_rotating_vectors(freqs, coefs)
        # circles = self.get_circles(vectors)

        ns = [10, 50, 250]
        approxs = VGroup(*[
            self.get_vector_sum_path(vectors[:n])
            for n in ns
        ])
        approxs.arrange(RIGHT, buff=2.5)
        approxs.set_height(3.75)
        approxs.to_edge(UP, buff=1.25)
        for a, c, w in zip(approxs, [BLUE, GREEN, YELLOW], [4, 3, 2]):
            a.set_stroke(c, w)
            a.set_stroke(WHITE, w + w / 2, background=True)

        labels = VGroup()
        for n, approx in zip(ns, approxs):
            label = TexMobject("n = ", str(n))
            label[1].match_color(approx)
            label.scale(2)
            label.next_to(approx, UP)
            label.to_edge(UP, buff=MED_SMALL_BUFF)
            labels.add(label)

        self.add(approxs)
        self.add(labels)

        return

        self.add_vectors_circles_path()
        n = 6
        self.circles[n:].set_opacity(0)
        self.circles[:n].set_stroke(width=3)
        path = self.drawn_path
        # path.set_stroke(BLACK, 8, background=True)
        # path = self.path
        # path.set_stroke(YELLOW, 5)
        # path.set_stroke(BLACK, 8, background=True)
        self.add(path, self.circles, self.vectors)

        self.update_mobjects(0)
