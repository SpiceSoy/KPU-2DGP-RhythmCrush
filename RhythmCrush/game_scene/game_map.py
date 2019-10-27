from ..game_scene.base_scene import *

from ..game_object.game_music import Music, Effect
from ..game_object.note import Note
from ..game_object.player_object import Player
from ..game_object.combo import Combo
from ..game_object.hp import Hp

from ..game_object.accuracy import *

from .. import ui

from .. import handler_set
from ..utill import input_manager

from ..utill.osu_file_format_parser import *


class NotePlayScene(BaseScene):
    def __init__(self, framework, music_tag):
        # 베이스 초기화
        super().__init__(framework)
        # 플레이할 음악
        self.music_tag = music_tag
        self.music = Music()
        # 효과음
        self.effect_don_normal = Effect()
        self.effect_don_hit = Effect()
        self.effect_kat_normal = Effect()
        self.effect_kat_hit = Effect()
        self.effect_combo_break = Effect()
        # 게임 맵
        self.map = MusicNoteMap()
        self.note_list = []
        # 플레이어 변수
        self.player = None
        # 최적화용 변수
        self.start_index = 0
        self.extra_update_count = 5
        self.extra_check_count = 10
        self.start_hit = 0
        # 콤보 카운터
        self.combo = Combo()
        # HP
        self.hp = Hp()
        # UI
        self.ui_combo_text = ui.UIText(1000, 50, self.combo.now_combo, pt=100)

    # 일단 Text URL 받게 설정
    def load(self):
        # 맵 파일 로드
        self.map = load_map_source(self.music_tag)
        # 노트 로드
        for note in self.map.get_hit_object():
            self.note_list.append(
                Note(
                    note[0], note[1], note[2], note[3], note[4],
                    (note[5], note[6], note[7], note[8]),
                    self.music.timer
                )
            )
        # 음악 로드
        self.music.load(self.music_tag + "/../" + self.map.get_props("AudioFilename"))
        # 효과음 로드
        self.effect_don_hit.load("Resource/Sound/don-hit.wav")
        self.effect_don_normal.load("Resource/Sound/don-normal.wav")
        self.effect_kat_hit.load("Resource/Sound/kat-hit.wav")
        self.effect_kat_normal.load("Resource/Sound/kat-normal.wav")
        self.effect_combo_break.load("Resource/Sound/combo-break.wav")
        # 플레이어 초기화
        self.player = Player()
        self.player.x = 100
        self.player.y = 400
        self.player.post_handler(self.input_handler)
        # 텍스트 로드
        self.ui_combo_text.load()


        self.post_note_handler()

    def start(self):
        super().start()
        self.music.start()
        self.start_index = 0

    def resume(self):
        super().start()
        self.music.resume()

    def pause(self):
        super().start()
        self.music.pause()

    def stop(self):
        super().stop()
        self.music.stop()

    def update(self, delta_time):
        count = self.extra_update_count
        if self.is_active:
            self.player.update(delta_time)

            for i in range(self.start_index, len(self.note_list)):
                note = self.note_list[i]
                if note.check_no_input():
                    self.hp.check(note.accuracy.grade)
                    if not self.combo.is_zero():
                        self.effect_combo_break.play()
                    self.combo.break_combo()
                if note.update(delta_time) is False:
                    count -= 1
                if note.time - self.music.timer.get_time_tick() < -500:
                    self.start_index = i
                if count < 0:
                    break;
            # UIUpdate
            self.ui_combo_text.update_text(str(self.combo.now_combo))

    def draw(self):
        if self.is_active:
            self.player.draw()

            for i in range(self.start_index, len(self.note_list)):
                note = self.note_list[i]
                if note.is_in_clipped():
                    note.draw()
                else:
                    if note.time - self.music.timer.get_time_tick() > 100:
                        break
            # UI Draw
            self.ui_combo_text.draw()

    def post_note_handler(self):
        def touch_type(type, hit, normal):
            def touch():
                ac = self.check_note_accuracy(type)
                self.hp.check(ac.grade)
                print(f"grade : {ac.grade} / diff_time : {ac.difference}")
                print(f"{str(self.combo)} / current_hp : {self.hp.get_hp()}")
                if ac.is_success():
                    hit.play()
                    self.combo.plus_combo()
                elif ac.is_fail():
                    if not self.combo.is_zero():
                        self.effect_combo_break.play()
                    self.combo.break_combo()
                else:
                    normal.play()
            return touch

        self.input_handler.add_handler(
            pico2d.SDL_KEYDOWN,
            handler_set.key_input(pico2d.SDLK_DOWN, touch_type(InputType.Don, self.effect_don_hit, self.effect_don_normal))
        )
        self.input_handler.add_handler(
            pico2d.SDL_KEYDOWN,
            handler_set.key_input(pico2d.SDLK_UP, touch_type(InputType.Kat, self.effect_kat_hit, self.effect_kat_normal))
        )

    def check_note_accuracy(self, player_input):
        count = self.extra_check_count
        if self.is_active:
            for i in range(self.start_index, len(self.note_list)):
                note = self.note_list[i]
                if not note.accuracy.is_gone():
                    acc = note.check_hit(player_input)
                    if acc.is_hit():
                        return acc
                    else:
                        count -= 1
                if count < 0:
                    return Accuracy()
            return Accuracy()
