"""Unit tests for HTML renderer."""

import unittest
from unittest.mock import Mock, MagicMock
from src.html_renderer import HtmlRenderer
from src.models import FamilyTree, Individual, Family


class TestHtmlRenderer(unittest.TestCase):
    """Test cases for HtmlRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tree = FamilyTree()
        self.renderer = HtmlRenderer(self.tree)
    
    def test_init(self):
        """Test renderer initialization."""
        self.assertEqual(self.renderer.tree, self.tree)
        self.assertEqual(len(self.renderer.rendered_individuals), 0)
    
    def test_render_empty_tree(self):
        """Test rendering an empty family tree."""
        html = self.renderer.render(title="Empty Tree")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<title>Empty Tree</title>", html)
        self.assertIn("alpinejs", html)  # Check Alpine.js is included
    
    def test_render_with_individuals(self):
        """Test rendering with individuals."""
        # Create test individuals
        ind1 = Individual("I001")
        ind1.given_name = "John"
        ind1.surname = "Doe"
        ind1.birth_date = "1 JAN 1950"
        ind1.death_date = "31 DEC 2020"
        ind1.sex = "M"
        
        ind2 = Individual("I002")
        ind2.given_name = "Jane"
        ind2.surname = "Doe"
        ind2.birth_date = "15 MAR 1952"
        ind2.sex = "F"
        
        self.tree.individuals = {"I001": ind1, "I002": ind2}
        
        # Create a family
        fam1 = Family("F001")
        fam1.husband_id = "I001"
        fam1.wife_id = "I002"
        fam1.marriage_date = "10 JUN 1975"
        
        self.tree.families = {"F001": fam1}
        
        html = self.renderer.render(title="Test Tree")
        
        # Check that individuals are rendered
        self.assertIn("John Doe", html)
        self.assertIn("Jane Doe", html)
        self.assertIn("b. 1 JAN 1950", html)
        self.assertIn("d. 31 DEC 2020", html)
        self.assertIn("m. 10 JUN 1975", html)
    
    def test_render_person_card(self):
        """Test rendering a person card."""
        ind = Individual("I001")
        ind.given_name = "Test"
        ind.surname = "Person"
        ind.birth_date = "1900"
        ind.death_date = "1980"
        ind.sex = "M"
        
        card_html = self.renderer._render_person_card(ind, "husband")
        
        # Check data attributes
        self.assertIn('data-person-id="I001"', card_html)
        self.assertIn('data-person-name="Test Person"', card_html)
        self.assertIn('data-birth-year="1900"', card_html)
        self.assertIn('data-death-year="1980"', card_html)
        self.assertIn('data-gender="M"', card_html)
        self.assertIn('data-role="husband"', card_html)
        self.assertIn('@click="showPersonDetails($el)"', card_html)
        
        # Check content
        self.assertIn("Test Person", card_html)
        self.assertIn("b. 1900", card_html)
        self.assertIn("d. 1980", card_html)
    
    def test_render_person_card_with_missing_data(self):
        """Test rendering person card with missing data."""
        ind = Individual("I001")
        # Missing name - don't set given_name or surname
        ind.birth_date = None
        ind.death_date = None
        
        card_html = self.renderer._render_person_card(ind, "child")
        
        # Should use ID as fallback for name
        self.assertIn("I001", card_html)
        self.assertIn('data-person-id="I001"', card_html)
        self.assertIn('data-gender="U"', card_html)  # Unknown gender
    
    def test_render_person_card_with_none_individual(self):
        """Test rendering with None individual."""
        card_html = self.renderer._render_person_card(None)
        self.assertIn("Missing Individual", card_html)
        self.assertIn("error", card_html)
    
    def test_find_root_families(self):
        """Test finding root families."""
        # Create individuals with parent-child relationships
        parent = Individual("I001")
        parent.given_name = "Parent"
        parent.family_spouse = ["F001"]
        
        child = Individual("I002")
        child.given_name = "Child"
        child.family_child = ["F001"]  # Has parents - should be a list
        child.family_spouse = ["F002"]
        
        grandchild = Individual("I003")
        grandchild.given_name = "Grandchild"
        grandchild.family_child = ["F002"]
        
        self.tree.individuals = {
            "I001": parent,
            "I002": child,
            "I003": grandchild
        }
        
        # Root family (parent has no parents)
        fam1 = Family("F001")
        fam1.husband_id = "I001"
        fam1.children_ids = ["I002"]
        
        # Non-root family (child has parents)
        fam2 = Family("F002")
        fam2.husband_id = "I002"
        fam2.children_ids = ["I003"]
        
        self.tree.families = {"F001": fam1, "F002": fam2}
        
        root_families = self.renderer._find_root_families()
        
        self.assertEqual(len(root_families), 1)
        self.assertEqual(root_families[0].id, "F001")
    
    def test_find_orphaned_individuals(self):
        """Test finding orphaned individuals."""
        # Connected individual
        connected = Individual("I001")
        connected.given_name = "Connected"
        
        # Orphaned individual (not in any family)
        orphan = Individual("I002")
        orphan.given_name = "Orphan"
        
        self.tree.individuals = {"I001": connected, "I002": orphan}
        
        # Family with connected individual
        fam = Family("F001")
        fam.husband_id = "I001"
        self.tree.families = {"F001": fam}
        
        orphans = self.renderer._find_orphaned_individuals()
        
        self.assertEqual(len(orphans), 1)
        self.assertEqual(orphans[0].id, "I002")
    
    def test_render_with_places(self):
        """Test rendering with birth and death places."""
        ind = Individual("I001")
        ind.given_name = "John"
        ind.surname = "Smith"
        ind.birth_place = "London, England"
        ind.death_place = "New York, USA"
        
        self.tree.individuals = {"I001": ind}
        
        html = self.renderer.render(include_places=True)
        self.assertIn("Born: London, England", html)
        self.assertIn("Died: New York, USA", html)
        
        # Test without places
        html_no_places = self.renderer.render(include_places=False)
        self.assertNotIn("Born: London, England", html_no_places)
        self.assertNotIn("Died: New York, USA", html_no_places)
    
    def test_render_with_photos(self):
        """Test rendering with photo objects."""
        ind = Individual("I001")
        ind.given_name = "Photo"
        ind.surname = "Person"
        ind.objects = ["photo.jpg", "document.pdf", "image.png"]
        
        self.tree.individuals = {"I001": ind}
        
        html = self.renderer.render(include_photos=True)
        self.assertIn('src="photo.jpg"', html)
        self.assertIn('alt="Photo of Photo Person"', html)
        
        # PDF should not be rendered as image
        self.assertNotIn('src="document.pdf"', html)
    
    def test_embedded_css(self):
        """Test that CSS is embedded inline."""
        html = self.renderer.render()
        
        # Check for embedded CSS
        self.assertIn("<style>", html)
        self.assertIn(":root {", html)
        self.assertIn("--primary-color:", html)
        self.assertIn(".person-card", html)
        
        # Should not have external CSS link
        self.assertNotIn('<link rel="stylesheet"', html)
    
    def test_alpine_js_integration(self):
        """Test Alpine.js integration."""
        html = self.renderer.render()
        
        # Check Alpine.js script inclusion
        self.assertIn("alpinejs", html)
        
        # Check Alpine.js directives
        self.assertIn('x-data="familyTreeApp()"', html)
        self.assertIn('x-init="init()"', html)
        self.assertIn('@click="expandAll()"', html)
        self.assertIn('@click="collapseAll()"', html)
        self.assertIn('x-model="searchQuery"', html)
        self.assertIn('x-show="showModal"', html)
    
    def test_error_handling_in_render(self):
        """Test error handling in main render method."""
        # Create a mock tree that will raise an exception
        mock_tree = Mock()
        mock_tree.families.values.side_effect = Exception("Test error")
        
        renderer = HtmlRenderer(mock_tree)
        html = renderer.render()
        
        # Should return error HTML
        self.assertIn("Error Rendering Family Tree", html)
        self.assertIn("Test error", html)
    
    def test_generation_of_javascript(self):
        """Test JavaScript generation."""
        js = self.renderer._generate_javascript()
        
        # Check for key functions
        self.assertIn("function familyTreeApp()", js)
        self.assertIn("expandAll()", js)
        self.assertIn("collapseAll()", js)
        self.assertIn("filterPeople()", js)
        self.assertIn("showPersonDetails(", js)
        self.assertIn("getPersonRelationships(", js)
        self.assertIn("navigateToPerson(", js)
    
    def test_render_children_sorting(self):
        """Test that children are sorted by birth year."""
        # Create children with different birth years
        child1 = Individual("I001")
        child1.given_name = "Youngest"
        child1.birth_date = "2000"
        
        child2 = Individual("I002")
        child2.given_name = "Oldest"
        child2.birth_date = "1990"
        
        child3 = Individual("I003")
        child3.given_name = "Middle"
        child3.birth_date = "1995"
        
        self.tree.individuals = {
            "I001": child1,
            "I002": child2,
            "I003": child3
        }
        
        family = Family("F001")
        family.children_ids = ["I001", "I002", "I003"]
        
        # Children should be sorted by birth year in output
        html = self.renderer._render_children(family)
        
        # Find positions of names in HTML
        pos_oldest = html.find("Oldest")
        pos_middle = html.find("Middle")
        pos_youngest = html.find("Youngest")
        
        # Oldest should appear first, then middle, then youngest
        self.assertTrue(pos_oldest < pos_middle < pos_youngest)


if __name__ == "__main__":
    unittest.main()