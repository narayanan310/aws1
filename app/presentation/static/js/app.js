document.addEventListener('alpine:init', () => {
  // Theme Store
  Alpine.store('theme', {
    current: localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
    toggle() {
      this.current = this.current === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', this.current);
    }
  });

  // Global Selection Store for Batch Operations
  Alpine.store('selection', {
    items: new Set(),
    lastSelected: null,
    
    toggle(id, event = null) {
      if (event && event.shiftKey && this.lastSelected) {
        // Shift-click logic would go here, relying on DOM order
        // This is complex without a framework managing the list, but we can do a DOM query
        this._selectRange(this.lastSelected, id);
      } else {
        if (this.items.has(id)) {
          this.items.delete(id);
        } else {
          this.items.add(id);
        }
        this.lastSelected = id;
      }
    },
    
    _selectRange(startId, endId) {
      const cards = Array.from(document.querySelectorAll('.masonry-item'));
      let startIndex = cards.findIndex(c => parseInt(c.dataset.id) === startId);
      let endIndex = cards.findIndex(c => parseInt(c.dataset.id) === endId);
      
      if (startIndex > endIndex) {
        [startIndex, endIndex] = [endIndex, startIndex];
      }
      
      for (let i = startIndex; i <= endIndex; i++) {
        this.items.add(parseInt(cards[i].dataset.id));
      }
    },
    
    clear() {
      this.items.clear();
      this.lastSelected = null;
    },
    
    selectAll() {
      document.querySelectorAll('.masonry-item').forEach(c => {
        this.items.add(parseInt(c.dataset.id));
      });
    },
    
    has(id) {
      return this.items.has(id);
    },
    
    get count() {
      return this.items.size;
    }
  });
});

// Shortcut Manager (Global Keydown)
document.addEventListener('keydown', (e) => {
  // Don't trigger shortcuts if user is typing in an input
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

  const selection = Alpine.store('selection');
  
  if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    selection.selectAll();
  } else if (e.key === 'Escape') {
    selection.clear();
    // Dispatch custom event to close modals/sidebars
    window.dispatchEvent(new CustomEvent('close-panels'));
  }
});
