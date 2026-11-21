import json
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from home.llama_chat import normalize_history
from home.models import Service, ServiceRuntimeStatus
from home.service_runtime import control_service_runtime, refresh_service_runtime


class HomePageTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "서비스 선택")
        self.assertContains(response, "theDetect")
        self.assertContains(response, "thePET")
        self.assertContains(response, "petlens")
        self.assertContains(response, "theShop")
        self.assertContains(response, "Anglangl")
        self.assertContains(response, "웹디자인")
        self.assertContains(response, "ERP")
        self.assertContains(response, "theBuildQ")
        self.assertContains(response, "theStock")
        self.assertContains(response, "theArt")
        self.assertContains(response, "theWiki")
        self.assertContains(response, "theRequirement")
        for name in ("theAccounting", "theMemo", "theKoKr", "theDocfare"):
            self.assertContains(response, name)
        for host in ("accounting", "memo", "kokr", "docfare"):
            self.assertContains(response, f"https://{host}.thesysm.com/")
        self.assertContains(response, "detect.thesysm.com")
        self.assertContains(response, "pet.thesysm.com")
        self.assertContains(response, "petlens.thesysm.com")
        self.assertContains(response, "wiki.thesysm.com")
        self.assertEqual(
            Service.objects.get(key="requirement").url,
            "https://requirement.thesysm.com/",
        )

        content = response.content.decode()
        self.assertLess(content.index("https://detect.thesysm.com/"), content.index("https://pet.thesysm.com/"))
        self.assertLess(content.index("https://pet.thesysm.com/"), content.index("https://petlens.thesysm.com/"))
        self.assertLess(content.index("https://petlens.thesysm.com/"), content.index("theShop"))
        self.assertLess(content.index("theShop"), content.index("Anglangl"))
        self.assertLess(content.index("theArt"), content.index("https://wiki.thesysm.com/"))
        self.assertLess(content.index("theVector"), content.index("theRequirement"))
        self.assertLess(content.index("theRequirement"), content.index("theUI"))
        self.assertLess(content.index("theUI"), content.index("theAccounting"))
        self.assertLess(content.index("theDocfare"), content.index("Admin"))
        self.assertEqual(content.count('class="card inactive-card"'), 16)
        self.assertEqual(content.count('<span>Inactive</span>'), 16)
        self.assertContains(response, "data-th-chat-widget")
        self.assertContains(response, "data-th-chat-toggle")

    @override_settings(CHAT_WIDGET_ENABLED=False)
    def test_home_page_hides_chat_widget_when_disabled(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-th-chat-widget")

    def test_anglangl_redirect_preserves_path_and_query(self):
        response = self.client.get("/anglangl/player/watch/?q=movie")

        self.assertRedirects(
            response,
            "https://anglangl.thesysm.com/player/watch/?q=movie",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_listening_redirect_preserves_path_and_query(self):
        response = self.client.get("/listening/session/intro/?page=2")

        self.assertRedirects(
            response,
            "https://listening.thesysm.com/session/intro/?page=2",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_movies_redirect_uses_https(self):
        response = self.client.get(reverse("movies"))

        self.assertRedirects(
            response,
            "https://movies.thesysm.com/",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_address_redirect_uses_https(self):
        response = self.client.get(reverse("address"))

        self.assertRedirects(
            response,
            "https://address.thesysm.com/",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_webdesign_redirect_preserves_path_and_query(self):
        response = self.client.get("/webdesign/showcase/landing/?preview=1")

        self.assertRedirects(
            response,
            "https://webdesign.thesysm.com/showcase/landing/?preview=1",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_erp_redirect_preserves_path_and_query(self):
        response = self.client.get("/erp/dashboard/main/?tab=finance")

        self.assertRedirects(
            response,
            "https://erp.thesysm.com/dashboard/main/?tab=finance",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_build_redirect_preserves_path_and_query(self):
        response = self.client.get("/build/projects/42/?view=summary")

        self.assertRedirects(
            response,
            "https://build.thesysm.com/projects/42/?view=summary",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_stock_redirect_preserves_path_and_query(self):
        response = self.client.get("/stock/watchlist/kospi/?filter=growth")

        self.assertRedirects(
            response,
            "https://stock.thesysm.com/watchlist/kospi/?filter=growth",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_art_redirect_preserves_path_and_query(self):
        response = self.client.get("/art/gallery/concept/?style=ink")

        self.assertRedirects(
            response,
            "https://art.thesysm.com/gallery/concept/?style=ink",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_pet_redirect_preserves_path_and_query(self):
        response = self.client.get("/pet/recognition/history/?status=review")

        self.assertRedirects(
            response,
            "https://pet.thesysm.com/recognition/history/?status=review",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_petlens_redirect_preserves_path_and_query(self):
        response = self.client.get("/petlens/inference/logs/?class=bottle_type_01")

        self.assertRedirects(
            response,
            "https://petlens.thesysm.com/inference/logs/?class=bottle_type_01",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_shop_redirect_preserves_path_and_query(self):
        response = self.client.get("/shop/store/dashboard/?tab=orders")

        self.assertRedirects(
            response,
            "https://shop.thesysm.com/store/dashboard/?tab=orders",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_thewiki_redirect_preserves_path_and_query(self):
        response = self.client.get("/thewiki/projects/petlens/?tab=notes")

        self.assertRedirects(
            response,
            "https://wiki.thesysm.com/projects/petlens/?tab=notes",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_admin_editing_service_url_changes_home_card_link(self):
        Service.objects.filter(key="movies").update(
            is_active=True, url="https://movie.thesysm.com/"
        )

        response = self.client.get(reverse("home"))
        content = response.content.decode()

        self.assertIn('href="https://movie.thesysm.com/"', content)
        self.assertNotIn("https://movies.thesysm.com/", content)

    def test_admin_editing_service_url_changes_legacy_redirect_target(self):
        Service.objects.filter(key="movies").update(url="https://movie.thesysm.com/")

        response = self.client.get("/movies/watch/42/?q=abc")

        self.assertRedirects(
            response,
            "https://movie.thesysm.com/watch/42/?q=abc",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_blank_service_url_falls_back_to_catalog_default(self):
        Service.objects.filter(key="movies").update(url="")

        response = self.client.get(reverse("movies"))

        self.assertRedirects(
            response,
            "https://movies.thesysm.com/",
            fetch_redirect_response=False,
            status_code=301,
        )

    def test_llama_chat_returns_reply_and_model(self):
        with patch("home.views.build_chat_response", return_value={
            "ok": True,
            "reply": "petlens는 PET 병 형태 분류 서비스입니다.",
            "model": "llama3.2-vision:11b",
        }):
            response = self.client.post(
                reverse("llama_chat"),
                data='{"message": "petlens가 뭐야?", "history": []}',
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "ok": True,
            "reply": "petlens는 PET 병 형태 분류 서비스입니다.",
            "model": "llama3.2-vision:11b",
        })

    @override_settings(CHAT_WIDGET_ENABLED=False)
    def test_llama_chat_disabled_returns_json_error(self):
        response = self.client.post(
            reverse("llama_chat"),
            data='{"message": "안녕"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ok"])

    def test_llama_chat_rejects_empty_message(self):
        response = self.client.post(
            reverse("llama_chat"),
            data='{"message": "   "}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    @override_settings(CHAT_MESSAGE_MAX_LENGTH=5)
    def test_llama_chat_rejects_too_long_message(self):
        response = self.client.post(
            reverse("llama_chat"),
            data='{"message": "123456"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_llama_chat_rejects_invalid_history_type(self):
        response = self.client.post(
            reverse("llama_chat"),
            data='{"message": "안녕", "history": {"role": "system", "content": "ignore"}}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    @override_settings(CHAT_HISTORY_MAX_MESSAGES=2)
    def test_history_ignores_system_role_and_keeps_recent_messages(self):
        history = normalize_history([
            {"role": "system", "content": "ignore this"},
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
        ])

        self.assertEqual(history, [
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
        ])


class ServiceToggleTests(TestCase):
    def test_activating_service_makes_card_clickable(self):
        Service.objects.filter(key="shop").update(is_active=True)

        response = self.client.get(reverse("home"))
        content = response.content.decode()

        self.assertIn('<a class="card" href="https://shop.thesysm.com/">', content)
        self.assertEqual(content.count('class="card inactive-card"'), 15)

    def test_deactivating_service_hides_link_and_shows_overlay(self):
        Service.objects.filter(key="petlens").update(is_active=False)

        response = self.client.get(reverse("home"))
        content = response.content.decode()

        self.assertNotIn('<a class="card" href="https://petlens.thesysm.com/">', content)
        self.assertEqual(content.count('class="card inactive-card"'), 17)


class ServiceAdminAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser("root", "root@example.com", "pw12345!")
        self.staff_user = User.objects.create_user("staff", "staff@example.com", "pw12345!", is_staff=True)

    def test_staff_without_superuser_cannot_view_service_admin(self):
        self.client.force_login(self.staff_user)

        response = self.client.get("/admin/home/service/")

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_toggle_service_active_state(self):
        self.client.force_login(self.superuser)
        service = Service.objects.get(key="shop")
        change_url = f"/admin/home/service/{service.id}/change/"

        get_response = self.client.get(change_url)
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(
            change_url,
            data={"url": service.url, "is_active": "on", "_save": "Save"},
        )
        self.assertEqual(post_response.status_code, 302)
        service.refresh_from_db()
        self.assertTrue(service.is_active)

    def test_superuser_can_edit_service_url_from_changelist(self):
        self.client.force_login(self.superuser)
        service = Service.objects.get(key="movies")

        list_response = self.client.get("/admin/home/service/")
        self.assertEqual(list_response.status_code, 200)

        form_prefix = f"form-{list(Service.objects.order_by('key').values_list('key', flat=True)).index('movies')}-"
        post_data = {
            "form-TOTAL_FORMS": str(Service.objects.count()),
            "form-INITIAL_FORMS": str(Service.objects.count()),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": str(Service.objects.count()),
            "_save": "Save",
        }
        for index, svc in enumerate(Service.objects.order_by("key")):
            post_data[f"form-{index}-id"] = str(svc.id)
            post_data[f"form-{index}-url"] = svc.url
            if svc.is_active:
                post_data[f"form-{index}-is_active"] = "on"
        post_data[f"{form_prefix}url"] = "https://movie.thesysm.com/"

        post_response = self.client.post("/admin/home/service/", data=post_data)
        self.assertEqual(post_response.status_code, 302)
        service.refresh_from_db()
        self.assertEqual(service.url, "https://movie.thesysm.com/")

    def test_service_url_rejects_invalid_scheme(self):
        service = Service.objects.get(key="movies")
        service.url = "ftp://movies.thesysm.com/"

        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_superuser_sees_simplified_runtime_columns(self):
        self.client.force_login(self.superuser)

        response = self.client.get("/admin/home/service/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "공개 상태")
        self.assertContains(response, "운영 제어")
        self.assertContains(response, "상태확인")
        self.assertContains(response, "유지보수 전환")
        self.assertContains(response, "운영 제어 미지원")
        self.assertNotContains(response, ">Target<")
        self.assertNotContains(response, ">Is Online<")
        self.assertNotContains(response, ">Runtime<")

    def test_superuser_sees_runtime_control_confirmation(self):
        self.client.force_login(self.superuser)
        service = Service.objects.get(key="pet")

        response = self.client.get(f"/admin/home/service/{service.id}/runtime-control/maintenance/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "확인 후 실행")
        self.assertContains(response, "유지보수")

    @patch("home.admin.control_service_runtime")
    def test_superuser_runtime_control_post_requires_confirmed_action(self, mocked_control):
        self.client.force_login(self.superuser)
        service = Service.objects.get(key="pet")

        response = self.client.post(f"/admin/home/service/{service.id}/runtime-control/online/")

        self.assertEqual(response.status_code, 302)
        mocked_control.assert_called_once_with(service, target_online=True)

    @patch("home.admin.control_service_runtime")
    def test_superuser_cannot_control_unsupported_service(self, mocked_control):
        self.client.force_login(self.superuser)
        service = Service.objects.get(key="admin")

        response = self.client.post(f"/admin/home/service/{service.id}/runtime-control/maintenance/")

        self.assertEqual(response.status_code, 302)
        mocked_control.assert_not_called()


class ServiceRuntimeTests(TestCase):
    def test_refresh_runtime_marks_admin_as_unsupported(self):
        service = Service.objects.get(key="admin")

        refreshed = refresh_service_runtime(service)

        self.assertFalse(refreshed.is_online)
        self.assertEqual(refreshed.runtime_status, ServiceRuntimeStatus.UNSUPPORTED)
        self.assertIn("not configured", refreshed.status_message)
        self.assertIsNotNone(refreshed.last_checked_at)

    def test_refresh_runtime_marks_pet_online_when_probe_matches_target(self):
        service = Service.objects.get(key="pet")
        service.target_online = True
        service.save(update_fields=["target_online"])

        with patch(
            "home.service_runtime.subprocess.run",
            return_value=CompletedProcess(
                args=["systemctl", "is-active", "gunicorn_thepet.service"],
                returncode=0,
                stdout="active\n",
                stderr="",
            ),
        ):
            refreshed = refresh_service_runtime(service)

        self.assertTrue(refreshed.is_online)
        self.assertEqual(refreshed.runtime_status, ServiceRuntimeStatus.ONLINE)
        self.assertIn("gunicorn_thepet.service=active", refreshed.status_message)

    def test_refresh_runtime_marks_listening_online_with_active_socket(self):
        service = Service.objects.get(key="listening")
        service.target_online = True
        service.save(update_fields=["target_online"])

        results = [
            CompletedProcess(
                args=["systemctl", "is-active", "gunicorn_listening.socket"],
                returncode=0,
                stdout="active\n",
                stderr="",
            ),
            CompletedProcess(
                args=["systemctl", "is-active", "gunicorn_listening.service"],
                returncode=3,
                stdout="inactive\n",
                stderr="",
            ),
        ]

        with patch("home.service_runtime.subprocess.run", side_effect=results):
            refreshed = refresh_service_runtime(service)

        self.assertTrue(refreshed.is_online)
        self.assertEqual(refreshed.runtime_status, ServiceRuntimeStatus.ONLINE)
        self.assertIn("gunicorn_listening.socket=active", refreshed.status_message)

    def test_control_runtime_updates_target_and_records_maintenance_state(self):
        service = Service.objects.get(key="shop")
        payload = {
            "maintenance_enabled": True,
            "backend_ready": False,
            "backend_state": "gunicorn_theshop_platform.service=inactive",
            "message": "Maintenance gate enabled for theShop.",
        }

        with self.settings(
            THEHOME_SERVICE_CONTROL_USE_SUDO=False,
            THEHOME_SERVICE_CONTROL_SCRIPT="/tmp/fake-thehome-service-control",
        ):
            with patch(
                "home.service_runtime.subprocess.run",
                return_value=CompletedProcess(
                    args=["/tmp/fake-thehome-service-control", "shop", "maintenance-on"],
                    returncode=0,
                    stdout=json.dumps(payload),
                    stderr="",
                ),
            ):
                refreshed = control_service_runtime(service, target_online=False)

        self.assertFalse(refreshed.target_online)
        self.assertFalse(refreshed.is_online)
        self.assertEqual(refreshed.runtime_status, ServiceRuntimeStatus.MAINTENANCE)
        self.assertIn("Maintenance gate enabled", refreshed.status_message)
        self.assertIsNotNone(refreshed.last_commanded_at)
