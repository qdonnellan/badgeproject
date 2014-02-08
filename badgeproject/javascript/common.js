
// Badge Award Handlers
$('.badge-actions').on('submit','.badge-award-form', function(e){
  e.preventDefault();
  var form = $(this).closest('form');
  var parent = $(form).closest('div[class="badge-actions"]');
  $(parent).html('<button class="btn btn-default disabled"><i class="icon-spinner icon-spin icon-large"></i> saving...</button>')
  $.ajax({
    type: form.attr('method'),
    url: form.attr('action'),
    data: form.serialize(),
    cache: false,
    success: function(data, status, xHTTP){
      $(parent).html(data);
    }
  });
  return false;
});

// Section Change Handlers
$('.section-list').on('submit','.change-section-form', function(e){
  e.preventDefault();
  var form = $(this).closest('form');
  var parent = $(form).closest('div[class="section-list"]');
  $.ajax({
    type: form.attr('method'),
    url: form.attr('action'),
    data: form.serialize(),
    cache: false,
    success: function(data, status, xHTTP){
      $(parent).html(data);
    }
  });
  return false;
});
