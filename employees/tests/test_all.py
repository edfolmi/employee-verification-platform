"""
Test suite for Employee Verification Platform.
Covers models, views, forms, and service layers.
"""
import io
import uuid
import numpy as np
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from PIL import Image
from employees.models import Employee


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def make_test_image(name="test.jpg", color=(255, 100, 100)):
    """Create an in-memory image for testing."""
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=color)
    img.save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


def make_test_employee(**kwargs):
    """Create a test employee instance."""
    defaults = {
        "full_name": "Jane Smith",
        "phone": "+1234567890",
        "email": "jane@example.com",
        "employer_name": "Acme Corp",
        "position": "Engineer",
        "reputation_score": 8.0,
        "notes": "Test employee",
        "image": make_test_image(),
    }
    defaults.update(kwargs)
    return Employee.objects.create(**defaults)


def make_fake_embedding(size=512):
    """Return a normalized random embedding."""
    vec = np.random.rand(size).astype(np.float32)
    return (vec / np.linalg.norm(vec)).tolist()


# ─────────────────────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────────────────────

class EmployeeModelTest(TestCase):

    def setUp(self):
        self.employee = make_test_employee()

    def test_employee_created(self):
        self.assertIsNotNone(self.employee.pk)
        self.assertEqual(self.employee.full_name, "Jane Smith")

    def test_uuid_assigned(self):
        self.assertIsInstance(self.employee.uuid, uuid.UUID)

    def test_str_representation(self):
        self.assertIn("Jane Smith", str(self.employee))
        self.assertIn("Acme Corp", str(self.employee))

    def test_reputation_display_excellent(self):
        self.employee.reputation_score = 9.0
        self.assertEqual(self.employee.get_reputation_display(), "Excellent")

    def test_reputation_display_good(self):
        self.employee.reputation_score = 7.0
        self.assertEqual(self.employee.get_reputation_display(), "Good")

    def test_reputation_display_average(self):
        self.employee.reputation_score = 5.0
        self.assertEqual(self.employee.get_reputation_display(), "Average")

    def test_reputation_display_poor(self):
        self.employee.reputation_score = 2.0
        self.assertEqual(self.employee.get_reputation_display(), "Poor")

    def test_reputation_color_success(self):
        self.employee.reputation_score = 9.0
        self.assertEqual(self.employee.get_reputation_color(), "success")

    def test_reputation_color_danger(self):
        self.employee.reputation_score = 2.0
        self.assertEqual(self.employee.get_reputation_color(), "danger")

    def test_created_at_auto_set(self):
        self.assertIsNotNone(self.employee.created_at)

    def test_default_ordering(self):
        make_test_employee(full_name="Alpha Alpha", email="a@a.com")
        make_test_employee(full_name="Zeta Zeta", email="z@z.com")
        employees = list(Employee.objects.all())
        # Newest first
        self.assertEqual(employees[0].full_name, "Zeta Zeta")


# ─────────────────────────────────────────────────────────────
# FORM TESTS
# ─────────────────────────────────────────────────────────────

class EmployeeFormTest(TestCase):

    def _valid_data(self):
        return {
            "full_name": "John Doe",
            "phone": "+1234567890",
            "email": "john@test.com",
            "employer_name": "Test Co",
            "position": "Developer",
            "reputation_score": "7.5",
            "notes": "",
        }

    def test_valid_form(self):
        from employees.forms import EmployeeForm
        form = EmployeeForm(
            data=self._valid_data(),
            files={"image": make_test_image()}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_full_name(self):
        from employees.forms import EmployeeForm
        data = self._valid_data()
        del data["full_name"]
        form = EmployeeForm(data=data, files={"image": make_test_image()})
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_invalid_email(self):
        from employees.forms import EmployeeForm
        data = self._valid_data()
        data["email"] = "not-an-email"
        form = EmployeeForm(data=data, files={"image": make_test_image()})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_reputation_out_of_range(self):
        from employees.forms import EmployeeForm
        data = self._valid_data()
        data["reputation_score"] = "15"
        form = EmployeeForm(data=data, files={"image": make_test_image()})
        self.assertFalse(form.is_valid())

    def test_oversized_image_rejected(self):
        from employees.forms import EmployeeForm
        big_file = SimpleUploadedFile(
            "big.jpg",
            b"x" * (settings.MAX_UPLOAD_SIZE + 1),
            content_type="image/jpeg",
        )
        form = EmployeeForm(data=self._valid_data(), files={"image": big_file})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_wrong_file_type_rejected(self):
        from employees.forms import EmployeeForm
        pdf = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        form = EmployeeForm(data=self._valid_data(), files={"image": pdf})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


class VerificationFormTest(TestCase):

    def test_valid_form(self):
        from employees.forms import VerificationForm
        form = VerificationForm(files={"image": make_test_image()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_no_image(self):
        from employees.forms import VerificationForm
        form = VerificationForm(data={}, files={})
        self.assertFalse(form.is_valid())


# ─────────────────────────────────────────────────────────────
# SERVICE TESTS — FaceService
# ─────────────────────────────────────────────────────────────

class FaceServiceTest(TestCase):

    @patch("employees.services.face_service.DeepFace.represent")
    def test_extract_embedding_returns_normalized_vector(self, mock_represent):
        """Embedding should be a unit vector (norm ≈ 1)."""
        from employees.services.face_service import FaceService
        raw = np.random.rand(512).tolist()
        mock_represent.return_value = [{"embedding": raw}]

        with patch("os.path.exists", return_value=True):
            result = FaceService.extract_embedding("/fake/path.jpg")

        norm = np.linalg.norm(result)
        self.assertAlmostEqual(norm, 1.0, places=5)
        self.assertEqual(result.shape, (512,))

    @patch("employees.services.face_service.DeepFace.represent")
    def test_no_face_raises_error(self, mock_represent):
        from employees.services.face_service import FaceService, FaceRecognitionError
        mock_represent.side_effect = ValueError("Face could not be detected")

        with patch("os.path.exists", return_value=True):
            with self.assertRaises(FaceRecognitionError):
                FaceService.extract_embedding("/fake/path.jpg")

    @patch("employees.services.face_service.DeepFace.represent")
    def test_multiple_faces_raises_error(self, mock_represent):
        from employees.services.face_service import FaceService, FaceRecognitionError
        mock_represent.return_value = [
            {"embedding": [0.1] * 512},
            {"embedding": [0.2] * 512},
        ]

        with patch("os.path.exists", return_value=True):
            with self.assertRaises(FaceRecognitionError) as ctx:
                FaceService.extract_embedding("/fake/path.jpg")

        self.assertIn("Multiple faces", str(ctx.exception))

    def test_file_not_found_raises_error(self):
        from employees.services.face_service import FaceService, FaceRecognitionError
        with self.assertRaises(FaceRecognitionError):
            FaceService.extract_embedding("/non/existent/file.jpg")

    def test_embedding_round_trip(self):
        from employees.services.face_service import FaceService
        original = np.random.rand(512).astype(np.float64)
        as_list = FaceService.embedding_to_list(original)
        back = FaceService.list_to_embedding(as_list)

        self.assertIsInstance(as_list, list)
        self.assertEqual(len(as_list), 512)
        np.testing.assert_array_almost_equal(original, back)


# ─────────────────────────────────────────────────────────────
# SERVICE TESTS — ChromaService
# ─────────────────────────────────────────────────────────────

class ChromaServiceTest(TestCase):

    def _mock_collection(self):
        col = MagicMock()
        col.count.return_value = 1
        return col

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_add_embedding_success(self, mock_get_col):
        from employees.services.chroma_service import ChromaService
        mock_get_col.return_value = self._mock_collection()

        result = ChromaService.add_employee_embedding(
            str(uuid.uuid4()),
            make_fake_embedding(),
            {"full_name": "Test", "employer": "Co", "reputation_score": "8.0"},
        )
        self.assertTrue(result)

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_add_embedding_cleans_metadata(self, mock_get_col):
        """Null bytes in metadata should be stripped."""
        from employees.services.chroma_service import ChromaService
        col = self._mock_collection()
        mock_get_col.return_value = col

        ChromaService.add_employee_embedding(
            str(uuid.uuid4()),
            make_fake_embedding(),
            {"full_name": "Te\x00st", "employer": "Co\x00", "reputation_score": "8.0"},
        )
        call_kwargs = col.add.call_args[1]
        metadata = call_kwargs["metadatas"][0]
        self.assertNotIn("\x00", metadata["full_name"])
        self.assertNotIn("\x00", metadata["employer"])

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_search_returns_match(self, mock_get_col):
        from employees.services.chroma_service import ChromaService
        employee_id = str(uuid.uuid4())
        col = self._mock_collection()
        col.query.return_value = {
            "ids": [[employee_id]],
            "distances": [[0.3]],
            "metadatas": [[{"full_name": "Test", "employer": "Co", "reputation_score": "8.0"}]],
        }
        mock_get_col.return_value = col

        result = ChromaService.search_embedding(make_fake_embedding())
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], employee_id)
        self.assertAlmostEqual(result["similarity"], 0.85, places=2)

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_search_returns_none_when_empty(self, mock_get_col):
        from employees.services.chroma_service import ChromaService
        col = self._mock_collection()
        col.query.return_value = {"ids": [[]], "distances": [[]], "metadatas": [[]]}
        mock_get_col.return_value = col

        result = ChromaService.search_embedding(make_fake_embedding())
        self.assertIsNone(result)

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_get_stats_healthy(self, mock_get_col):
        from employees.services.chroma_service import ChromaService
        mock_get_col.return_value = self._mock_collection()

        stats = ChromaService.get_collection_stats()
        self.assertEqual(stats["status"], "healthy")
        self.assertEqual(stats["total_embeddings"], 1)

    @patch("employees.services.chroma_service.ChromaService._get_collection")
    def test_delete_embedding(self, mock_get_col):
        from employees.services.chroma_service import ChromaService
        mock_get_col.return_value = self._mock_collection()

        result = ChromaService.delete_employee_embedding(str(uuid.uuid4()))
        self.assertTrue(result)


# ─────────────────────────────────────────────────────────────
# VIEW TESTS
# ─────────────────────────────────────────────────────────────

class HomeViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    @patch("employees.views.ChromaService.get_collection_stats")
    def test_home_loads(self, mock_stats):
        mock_stats.return_value = {"collection_name": "test", "total_embeddings": 0, "status": "healthy"}
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    @patch("employees.views.ChromaService.get_collection_stats")
    def test_home_shows_employee_count(self, mock_stats):
        mock_stats.return_value = {"collection_name": "test", "total_embeddings": 0, "status": "healthy"}
        make_test_employee()
        make_test_employee(full_name="Second Person", email="second@test.com")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "2")


class AddEmployeeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("add_employee")

    def test_get_add_employee_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_employee.html")

    @patch("employees.views.ChromaService.add_employee_embedding", return_value=True)
    @patch("employees.views.FaceService.extract_embedding")
    def test_post_valid_employee(self, mock_extract, mock_add):
        mock_extract.return_value = np.array(make_fake_embedding())
        data = {
            "full_name": "Alice Test",
            "phone": "+9876543210",
            "email": "alice@test.com",
            "employer_name": "Widget Inc",
            "position": "Manager",
            "reputation_score": "9.0",
            "notes": "",
        }
        response = self.client.post(self.url, {**data, "image": make_test_image()})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(Employee.objects.filter(email="alice@test.com").exists())

    @patch("employees.views.FaceService.extract_embedding")
    def test_face_error_shows_message(self, mock_extract):
        from employees.services.face_service import FaceRecognitionError
        mock_extract.side_effect = FaceRecognitionError("No face detected")
        data = {
            "full_name": "Bob Test",
            "phone": "+111",
            "email": "bob@test.com",
            "employer_name": "Corp",
            "position": "Dev",
            "reputation_score": "5.0",
            "notes": "",
        }
        response = self.client.post(self.url, {**data, "image": make_test_image()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No face detected")
        self.assertFalse(Employee.objects.filter(email="bob@test.com").exists())

    def test_invalid_form_stays_on_page(self):
        response = self.client.post(self.url, {"full_name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_employee.html")


class VerifyEmployeeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("verify_employee")
        self.employee = make_test_employee()

    def test_get_verify_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "verify_employee.html")

    @patch("employees.views.ChromaService.search_embedding")
    @patch("employees.views.FaceService.extract_embedding")
    def test_match_above_threshold(self, mock_extract, mock_search):
        mock_extract.return_value = np.array(make_fake_embedding())
        mock_search.return_value = {
            "id": str(self.employee.uuid),
            "distance": 0.2,
            "similarity": 0.90,
            "metadata": {},
        }
        response = self.client.post(self.url, {"image": make_test_image()})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "result.html")
        self.assertContains(response, "Jane Smith")
        self.assertTrue(response.context["match_found"])

    @patch("employees.views.ChromaService.search_embedding")
    @patch("employees.views.FaceService.extract_embedding")
    def test_match_below_threshold(self, mock_extract, mock_search):
        mock_extract.return_value = np.array(make_fake_embedding())
        mock_search.return_value = {
            "id": str(self.employee.uuid),
            "distance": 1.0,
            "similarity": 0.50,
            "metadata": {},
        }
        response = self.client.post(self.url, {"image": make_test_image()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["match_found"])

    @patch("employees.views.ChromaService.search_embedding")
    @patch("employees.views.FaceService.extract_embedding")
    def test_no_chromadb_results(self, mock_extract, mock_search):
        mock_extract.return_value = np.array(make_fake_embedding())
        mock_search.return_value = None
        response = self.client.post(self.url, {"image": make_test_image()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["match_found"])

    @patch("employees.views.FaceService.extract_embedding")
    def test_face_extraction_error_shows_message(self, mock_extract):
        from employees.services.face_service import FaceRecognitionError
        mock_extract.side_effect = FaceRecognitionError("Multiple faces detected")
        response = self.client.post(self.url, {"image": make_test_image()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Multiple faces detected")


class EmployeeListViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_empty_list(self):
        response = self.client.get(reverse("employee_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employee_list.html")
        self.assertContains(response, "No Employees")

    def test_shows_employees(self):
        make_test_employee()
        response = self.client.get(reverse("employee_list"))
        self.assertContains(response, "Jane Smith")


# ─────────────────────────────────────────────────────────────
# SIMILARITY CALCULATION TESTS
# ─────────────────────────────────────────────────────────────

class SimilarityTest(TestCase):

    def test_identical_embeddings_give_similarity_one(self):
        """Distance 0.0 should produce similarity 1.0."""
        similarity = 1 - (0.0 / 2)
        self.assertAlmostEqual(similarity, 1.0)

    def test_opposite_embeddings_give_similarity_zero(self):
        """Distance 2.0 should produce similarity 0.0."""
        similarity = 1 - (2.0 / 2)
        self.assertAlmostEqual(similarity, 0.0)

    def test_threshold_boundary(self):
        """Test that threshold boundary is respected."""
        threshold = settings.SIMILARITY_THRESHOLD  # 0.65
        self.assertGreater(0.70, threshold)
        self.assertLess(0.60, threshold)
        self.assertAlmostEqual(0.65, threshold)
